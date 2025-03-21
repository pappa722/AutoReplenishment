# frontend/src/components/inventory/SlowMovingItems.vue
<template>
  <div class="slow-moving-items">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>滞销商品分析</span>
          <div class="header-actions">
            <el-select v-model="timeRange" size="small" style="width: 150px; margin-right: 10px;">
              <el-option label="最近30天" value="30" />
              <el-option label="最近90天" value="90" />
              <el-option label="最近180天" value="180" />
              <el-option label="最近365天" value="365" />
            </el-select>
            <el-select v-model="categoryFilter" placeholder="商品分类" clearable size="small" style="width: 150px; margin-right: 10px;">
              <el-option
                v-for="category in categories"
                :key="category.value"
                :label="category.label"
                :value="category.value"
              />
            </el-select>
            <el-button-group>
              <el-button size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button size="small" @click="exportData">
                <el-icon><Download /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 滞销商品概览 -->
      <div class="overview-section">
        <el-row :gutter="20">
          <el-col :span="6" v-for="metric in slowMovingMetrics" :key="metric.label">
            <el-card shadow="hover" :body-style="{ padding: '15px' }">
              <div class="metric-item">
                <div class="metric-value" :class="getMetricClass(metric)">
                  {{ formatMetricValue(metric) }}
                  <span class="metric-unit">{{ metric.unit }}</span>
                </div>
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-change" :class="metric.trend">
                  {{ metric.change }}%
                  <span>较上期</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 滞销原因分布 -->
      <div class="reason-distribution">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="chart-header">
                  <span>滞销原因分布</span>
                  <el-tooltip
                    effect="dark"
                    content="展示不同原因导致的滞销商品数量分布"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <div class="reason-chart" ref="reasonChartRef"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="chart-header">
                  <span>滞销商品库存价值分布</span>
                  <el-tooltip
                    effect="dark"
                    content="展示不同类型滞销商品的库存价值占比"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <div class="value-chart" ref="valueChartRef"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 滞销趋势分析 -->
      <div class="trend-analysis">
        <el-card class="chart-card">
          <template #header>
            <div class="chart-header">
              <span>滞销趋势分析</span>
              <div class="chart-actions">
                <el-radio-group v-model="trendType" size="small">
                  <el-radio-button label="count">商品数量</el-radio-button>
                  <el-radio-button label="value">库存价值</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="trend-chart" ref="trendChartRef"></div>
        </el-card>
      </div>

      <!-- 滞销商品明细 -->
      <div class="detail-section">
        <el-card>
          <template #header>
            <div class="detail-header">
              <span>滞销商品明细</span>
              <div class="detail-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索商品..."
                  prefix-icon="Search"
                  clearable
                  size="small"
                  style="width: 200px; margin-right: 10px;"
                />
                <el-select
                  v-model="reasonFilter"
                  placeholder="滞销原因"
                  clearable
                  size="small"
                  style="width: 150px; margin-right: 10px;"
                >
                  <el-option label="季节性商品" value="seasonal" />
                  <el-option label="过量采购" value="over_purchase" />
                  <el-option label="市场需求变化" value="demand_change" />
                  <el-option label="替代品出现" value="substitution" />
                  <el-option label="其他原因" value="others" />
                </el-select>
                <el-select
                  v-model="statusFilter"
                  placeholder="处理状态"
                  clearable
                  size="small"
                  style="width: 150px; margin-right: 10px;"
                >
                  <el-option label="待处理" value="pending" />
                  <el-option label="处理中" value="processing" />
                  <el-option label="已处理" value="completed" />
                </el-select>
              </div>
            </div>
          </template>
          
          <el-table
            :data="filteredSlowMovingItems"
            style="width: 100%"
            :max-height="400"
            v-loading="loading"
          >
            <el-table-column prop="product_code" label="商品编码" width="120" sortable />
            <el-table-column prop="product_name" label="商品名称" width="150" sortable />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="slow_moving_days" label="滞销天数" width="100" sortable>
              <template #default="{ row }">
                <span :class="getSlowMovingClass(row.slow_moving_days)">
                  {{ row.slow_moving_days }}天
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="last_sale_date" label="最后销售" width="120" sortable />
            <el-table-column prop="current_stock" label="当前库存" width="100" sortable />
            <el-table-column prop="inventory_value" label="库存价值" width="120" sortable>
              <template #default="{ row }">
                {{ formatCurrency(row.inventory_value) }}
              </template>
            </el-table-column>
            <el-table-column prop="slow_moving_reason" label="滞销原因" width="120">
              <template #default="{ row }">
                <el-tag :type="getReasonType(row.slow_moving_reason)" effect="plain">
                  {{ row.slow_moving_reason }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="suggested_action" label="建议措施" width="150" />
            <el-table-column prop="status" label="处理状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button 
                    size="small" 
                    :type="row.status === '待处理' ? 'primary' : 'success'"
                    @click="handleAction(row)"
                  >
                    {{ row.status === '待处理' ? '处理' : '查看' }}
                  </el-button>
                  <el-button
                    size="small"
                    @click="showHistory(row)"
                  >
                    记录
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="totalItems"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 处理记录对话框 -->
    <el-dialog
      v-model="historyDialogVisible"
      title="处理记录"
      width="60%"
    >
      <div v-if="selectedProduct">
        <el-timeline>
          <el-timeline-item
            v-for="(activity, index) in selectedProduct.history"
            :key="index"
            :type="getActivityType(activity.action)"
            :timestamp="activity.time"
          >
            <h4>{{ activity.action }}</h4>
            <p>{{ activity.description }}</p>
            <p v-if="activity.result" class="activity-result">
              处理结果：{{ activity.result }}
            </p>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { Refresh, Download, QuestionFilled } from '@element-plus/icons-vue';

export default {
  name: 'SlowMovingItems',
  components: {
    Refresh,
    Download,
    QuestionFilled
  },
  setup() {
    // 状态定义
    const loading = ref(false);
    const timeRange = ref('90');
    const categoryFilter = ref('');
    const reasonChartRef = ref(null);
    const valueChartRef = ref(null);
    const trendChartRef = ref(null);
    const trendType = ref('count');
    const searchQuery = ref('');
    const reasonFilter = ref('');
    const statusFilter = ref('');
    const currentPage = ref(1);
    const pageSize = ref(20);
    const totalItems = ref(100);
    const historyDialogVisible = ref(false);
    const selectedProduct = ref(null);

    // 模拟数据
    const categories = ref([
      { value: 'food', label: '食品' },
      { value: 'drink', label: '饮料' },
      { value: 'daily', label: '日用品' }
    ]);

    const slowMovingMetrics = ref([
      {
        label: '滞销商品数',
        value: 125,
        unit: '个',
        trend: 'down',
        change: -15.3,
        target: 100,
        type: 'count'
      },
      {
        label: '滞销率',
        value: 8.5,
        unit: '%',
        trend: 'down',
        change: -2.1,
        target: 5,
        type: 'percentage'
      },
      {
        label: '滞销商品库存价值',
        value: 256000,
        unit: '元',
        trend: 'down',
        change: -12.4,
        target: 200000,
        type: 'currency'
      },
      {
        label: '库存价值占比',
        value: 12.8,
        unit: '%',
        trend: 'down',
        change: -1.5,
        target: 10,
        type: 'percentage'
      }
    ]);

    // 方法定义
    const formatMetricValue = (metric) => {
      switch (metric.type) {
        case 'currency':
          return new Intl.NumberFormat('zh-CN', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
          }).format(metric.value);
        case 'percentage':
          return metric.value.toFixed(1);
        default:
          return metric.value;
      }
    };

    const getMetricClass = (metric) => {
      if (metric.type === 'percentage' || metric.type === 'currency') {
        return metric.value <= metric.target ? 'good' : 'bad';
      }
      return metric.value <= metric.target ? 'good' : 'bad';
    };

    const initReasonChart = () => {
      if (!reasonChartRef.value) return;
      
      const chart = echarts.init(reasonChartRef.value);
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '20',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: 35, name: '季节性商品' },
              { value: 25, name: '过量采购' },
              { value: 20, name: '市场需求变化' },
              { value: 15, name: '替代品出现' },
              { value: 5, name: '其他原因' }
            ]
          }
        ]
      };
      chart.setOption(option);
    };

    const initValueChart = () => {
      if (!valueChartRef.value) return;
      
      const chart = echarts.init(valueChartRef.value);
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function(params) {
            const data = params[0];
            return `${data.name}<br/>库存价值：${formatCurrency(data.value)}<br/>占比：${data.value2}%`;
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '库存价值（元）',
          axisLabel: {
            formatter: value => formatShortNumber(value)
          }
        },
        yAxis: {
          type: 'category',
          data: ['长期积压', '季节性滞销', '临时性滞销', '结构性滞销']
        },
        series: [
          {
            type: 'bar',
            data: [
              { value: 120000, value2: 35 },
              { value: 85000, value2: 25 },
              { value: 65000, value2: 20 },
              { value: 45000, value2: 15 }
            ],
            itemStyle: {
              color: function(params) {
                const colors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a'];
                return colors[params.dataIndex];
              }
            },
            label: {
              show: true,
              position: 'right',
              formatter: function(params) {
                return params.data.value2 + '%';
              }
            }
          }
        ]
      };
      chart.setOption(option);
    };

    const formatCurrency = (value) => {
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    };

    const formatShortNumber = (value) => {
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万';
      }
      return value;
    };

    // 生命周期钩子
    onMounted(() => {
      initReasonChart();
      initValueChart();
    });

    // 监听器
    watch([timeRange, categoryFilter], () => {
      loading.value = true;
      // 模拟加载数据
      setTimeout(() => {
        initReasonChart();
        initValueChart();
        loading.value = false;
      }, 800);
    });

    // 事件处理方法
    const refreshData = () => {
      loading.value = true;
      setTimeout(() => {
        initReasonChart();
        initValueChart();
        loading.value = false;
        ElMessage.success('数据已更新');
      }, 800);
    };

    const exportData = () => {
      ElMessage.success('数据导出成功');
    };

    // 滞销商品数据
    const slowMovingItems = ref([
      {
        product_code: 'SKU001',
        product_name: '夏季短袖T恤',
        category: '服装',
        slow_moving_days: 120,
        last_sale_date: '2023-11-15',
        current_stock: 350,
        inventory_value: 17500,
        slow_moving_reason: '季节性商品',
        suggested_action: '季末清仓促销',
        status: '待处理',
        history: [
          {
            time: '2024-03-21 15:30',
            action: '识别为滞销品',
            description: '系统自动识别为滞销商品，已超过90天无销售记录。',
            result: null
          }
        ]
      },
      {
        product_code: 'SKU002',
        product_name: '保温水杯',
        category: '日用品',
        slow_moving_days: 85,
        last_sale_date: '2023-12-20',
        current_stock: 200,
        inventory_value: 12000,
        slow_moving_reason: '过量采购',
        suggested_action: '建议打折促销',
        status: '处理中',
        history: [
          {
            time: '2024-03-21 15:30',
            action: '识别为滞销品',
            description: '系统自动识别为滞销商品，库存周转率低于预警阈值。',
            result: null
          },
          {
            time: '2024-03-21 16:00',
            action: '启动促销',
            description: '制定促销方案：买一送一活动。',
            result: '待执行'
          }
        ]
      }
    ]);

    // 计算属性
    const filteredSlowMovingItems = computed(() => {
      let filtered = [...slowMovingItems.value];
      
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        filtered = filtered.filter(item => 
          item.product_code.toLowerCase().includes(query) ||
          item.product_name.toLowerCase().includes(query)
        );
      }

      if (categoryFilter.value) {
        filtered = filtered.filter(item => 
          item.category === categoryFilter.value
        );
      }

      if (reasonFilter.value) {
        filtered = filtered.filter(item => 
          item.slow_moving_reason === reasonFilter.value
        );
      }

      if (statusFilter.value) {
        filtered = filtered.filter(item => 
          item.status === statusFilter.value
        );
      }

      return filtered;
    });

    // 趋势图表初始化
    const initTrendChart = () => {
      if (!trendChartRef.value) return;
      
      const chart = echarts.init(trendChartRef.value);
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: ['新增滞销', '处理完成', '净增长']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月', '5月', '6月']
        },
        yAxis: {
          type: 'value',
          name: trendType.value === 'count' ? '商品数量' : '库存价值(万元)'
        },
        series: [
          {
            name: '新增滞销',
            type: 'bar',
            stack: 'total',
            data: trendType.value === 'count' 
              ? [20, 25, 18, 22, 15, 12]
              : [15, 18, 12, 16, 10, 8]
          },
          {
            name: '处理完成',
            type: 'bar',
            stack: 'total',
            data: trendType.value === 'count'
              ? [-15, -20, -12, -18, -10, -8]
              : [-10, -15, -8, -12, -7, -5]
          },
          {
            name: '净增长',
            type: 'line',
            data: trendType.value === 'count'
              ? [5, 5, 6, 4, 5, 4]
              : [5, 3, 4, 4, 3, 3]
          }
        ]
      };
      chart.setOption(option);
    };

    // 辅助方法
    const getSlowMovingClass = (days) => {
      if (days >= 180) return 'very-slow';
      if (days >= 90) return 'slow';
      if (days >= 60) return 'medium-slow';
      return 'slight-slow';
    };

    const getReasonType = (reason) => {
      switch (reason) {
        case '季节性商品':
          return 'warning';
        case '过量采购':
          return 'danger';
        case '市场需求变化':
          return 'info';
        case '替代品出现':
          return '';
        default:
          return 'info';
      }
    };

    const getStatusType = (status) => {
      switch (status) {
        case '待处理':
          return 'danger';
        case '处理中':
          return 'warning';
        case '已处理':
          return 'success';
        default:
          return 'info';
      }
    };

    const getActivityType = (action) => {
      if (action.includes('识别')) return 'warning';
      if (action.includes('促销')) return 'primary';
      if (action.includes('完成')) return 'success';
      return 'info';
    };

    // 事件处理方法
    const handleAction = (row) => {
      ElMessage.success(`开始处理商品：${row.product_name}`);
    };

    const showHistory = (row) => {
      selectedProduct.value = row;
      historyDialogVisible.value = true;
    };

    const handleSizeChange = (val) => {
      pageSize.value = val;
      // 重新加载数据
    };

    const handleCurrentChange = (val) => {
      currentPage.value = val;
      // 重新加载数据
    };

    // 监听趋势图类型变化
    watch(trendType, () => {
      initTrendChart();
    });

    // 在mounted中添加趋势图初始化
    onMounted(() => {
      initReasonChart();
      initValueChart();
      initTrendChart();
    });

    return {
      loading,
      timeRange,
      categoryFilter,
      categories,
      slowMovingMetrics,
      reasonChartRef,
      valueChartRef,
      trendChartRef,
      trendType,
      searchQuery,
      reasonFilter,
      statusFilter,
      currentPage,
      pageSize,
      totalItems,
      historyDialogVisible,
      selectedProduct,
      slowMovingItems,
      filteredSlowMovingItems,
      formatMetricValue,
      getMetricClass,
      getSlowMovingClass,
      getReasonType,
      getStatusType,
      getActivityType,
      handleAction,
      showHistory,
      handleSizeChange,
      handleCurrentChange,
      refreshData,
      exportData
    };
  }
};
</script>

<style scoped>
.slow-moving-items {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.overview-section {
  margin-bottom: 30px;
}

.metric-item {
  text-align: center;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.metric-value.good {
  color: #67c23a;
}

.metric-value.bad {
  color: #f56c6c;
}

.metric-unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
  margin-left: 4px;
}

.metric-label {
  color: #606266;
  font-size: 14px;
}

.metric-change {
  font-size: 12px;
  margin-top: 5px;
}

.metric-change.up {
  color: #67c23a;
}

.metric-change.down {
  color: #f56c6c;
}

.metric-change span {
  color: #909399;
  margin-left: 4px;
}

.reason-distribution {
  margin-bottom: 30px;
}

.chart-card {
  height: 400px;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reason-chart,
.value-chart,
.trend-chart {
  height: 320px;
  width: 100%;
}

.trend-analysis {
  margin-bottom: 30px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-actions {
  display: flex;
  align-items: center;
}

.very-slow {
  color: #f56c6c;
  font-weight: bold;
}

.slow {
  color: #e6a23c;
  font-weight: bold;
}

.medium-slow {
  color: #409eff;
  font-weight: bold;
}

.slight-slow {
  color: #67c23a;
  font-weight: bold;
}

.activity-result {
  color: #409eff;
  margin-top: 5px;
  font-size: 13px;
}

:deep(.el-card__header) {
  padding: 15px 20px;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>