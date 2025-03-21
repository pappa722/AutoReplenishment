# frontend/src/components/inventory/TurnoverAnalysis.vue
<template>
  <div class="turnover-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>商品周转率分析</span>
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
      
      <!-- 周转率概览 -->
      <div class="turnover-overview">
        <el-row :gutter="20">
          <el-col :span="6" v-for="metric in turnoverMetrics" :key="metric.label">
            <el-card :body-style="{ padding: '15px' }" shadow="hover">
              <div class="metric-item">
                <div class="metric-value" :class="getMetricClass(metric)">
                  {{ metric.value }}
                  <span class="metric-unit">{{ metric.unit }}</span>
                </div>
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-change" :class="metric.trend">
                  {{ metric.change }}%
                  <span>较上周期</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <!-- 周转率分布图 -->
      <div class="turnover-charts">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-container">
              <div class="chart-title">周转率分布</div>
              <div class="distribution-chart" ref="distributionChartRef"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <div class="chart-title">周转率与库存价值关系</div>
              <div class="scatter-chart" ref="scatterChartRef"></div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 周转率趋势图 -->
      <div class="turnover-trend">
        <div class="chart-title">周转率趋势</div>
        <div class="trend-chart" ref="trendChartRef"></div>
      </div>
      
      <!-- 商品周转率明细表 -->
      <div class="turnover-details">
        <div class="table-title">商品周转率明细</div>
        <div class="table-actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索商品..."
            prefix-icon="Search"
            clearable
            size="small"
            style="width: 200px; margin-right: 10px;"
          />
          <el-select
            v-model="turnoverFilter"
            placeholder="周转率范围"
            clearable
            size="small"
            style="width: 150px; margin-right: 10px;"
          >
            <el-option label="高周转(>12)" value="high" />
            <el-option label="中周转(6-12)" value="medium" />
            <el-option label="低周转(3-6)" value="low" />
            <el-option label="极低周转(<3)" value="very_low" />
          </el-select>
        </div>
        <el-table
          :data="filteredProductList"
          style="width: 100%"
          :max-height="400"
          v-loading="loading"
        >
          <el-table-column prop="product_code" label="商品编码" width="120" sortable />
          <el-table-column prop="product_name" label="商品名称" width="150" sortable />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="turnover_rate" label="周转率" width="100" sortable>
            <template #default="{ row }">
              <span :class="getTurnoverRateClass(row.turnover_rate)">
                {{ row.turnover_rate.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="turnover_days" label="周转天数" width="100" sortable>
            <template #default="{ row }">
              {{ row.turnover_days }} 天
            </template>
          </el-table-column>
          <el-table-column prop="average_inventory" label="平均库存" width="100" sortable />
          <el-table-column prop="inventory_value" label="库存价值" width="120" sortable>
            <template #default="{ row }">
              {{ formatCurrency(row.inventory_value) }}
            </template>
          </el-table-column>
          <el-table-column prop="sales_quantity" label="销售量" width="100" sortable />
          <el-table-column prop="sales_value" label="销售额" width="120" sortable>
            <template #default="{ row }">
              {{ formatCurrency(row.sales_value) }}
            </template>
          </el-table-column>
          <el-table-column prop="abc_class" label="ABC分类" width="100">
            <template #default="{ row }">
              <el-tag :type="getAbcClassType(row.abc_class)" effect="plain">
                {{ row.abc_class }}类
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="suggested_action" label="建议操作" />
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
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { Refresh, Download, Search } from '@element-plus/icons-vue';

export default {
  name: 'TurnoverAnalysis',
  components: {
    Refresh,
    Download,
    Search
  },
  setup() {
    // 状态定义
    const loading = ref(false);
    const timeRange = ref('90');
    const categoryFilter = ref('');
    const turnoverFilter = ref('');
    const searchQuery = ref('');
    const distributionChartRef = ref(null);
    const scatterChartRef = ref(null);
    const trendChartRef = ref(null);
    const currentPage = ref(1);
    const pageSize = ref(20);
    const totalItems = ref(100);

    // 模拟数据
    const categories = ref([
      { value: 'food', label: '食品' },
      { value: 'drink', label: '饮料' },
      { value: 'daily', label: '日用品' }
    ]);

    const turnoverMetrics = ref([
      {
        label: '平均周转率',
        value: 8.5,
        unit: '次/年',
        trend: 'up',
        change: 12.4,
        target: 10
      },
      {
        label: '平均周转天数',
        value: 42.9,
        unit: '天',
        trend: 'down',
        change: -10.2,
        target: 36
      },
      {
        label: '库存周转资金',
        value: 1250000,
        unit: '元',
        trend: 'down',
        change: -5.8,
        target: 1000000
      },
      {
        label: '低周转SKU占比',
        value: 25.4,
        unit: '%',
        trend: 'down',
        change: -3.2,
        target: 20
      }
    ]);

    const productList = ref([
      {
        product_code: 'SKU001',
        product_name: '高端牛奶',
        category: '饮料',
        turnover_rate: 15.8,
        turnover_days: 23,
        average_inventory: 500,
        inventory_value: 25000,
        sales_quantity: 7900,
        sales_value: 395000,
        abc_class: 'A',
        suggested_action: '维持当前库存水平，周转率良好'
      },
      {
        product_code: 'SKU002',
        product_name: '巧克力饼干',
        category: '食品',
        turnover_rate: 12.4,
        turnover_days: 29,
        average_inventory: 450,
        inventory_value: 13500,
        sales_quantity: 5580,
        sales_value: 167400,
        abc_class: 'A',
        suggested_action: '维持当前库存水平，周转率良好'
      },
      {
        product_code: 'SKU003',
        product_name: '洗发水',
        category: '日用品',
        turnover_rate: 8.2,
        turnover_days: 44,
        average_inventory: 300,
        inventory_value: 18000,
        sales_quantity: 2460,
        sales_value: 147600,
        abc_class: 'B',
        suggested_action: '适当减少库存，提高周转率'
      },
      {
        product_code: 'SKU004',
        product_name: '纸巾',
        category: '日用品',
        turnover_rate: 4.5,
        turnover_days: 81,
        average_inventory: 800,
        inventory_value: 16000,
        sales_quantity: 3600,
        sales_value: 72000,
        abc_class: 'C',
        suggested_action: '大幅减少库存，考虑调整订货周期'
      },
      {
        product_code: 'SKU005',
        product_name: '牙膏',
        category: '日用品',
        turnover_rate: 2.1,
        turnover_days: 174,
        average_inventory: 500,
        inventory_value: 10000,
        sales_quantity: 1050,
        sales_value: 21000,
        abc_class: 'C',
        suggested_action: '严重积压，建议清理库存或促销'
      }
    ]);

    // 计算属性
    const filteredProductList = computed(() => {
      let filtered = [...productList.value];
      
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

      if (turnoverFilter.value) {
        switch (turnoverFilter.value) {
          case 'high':
            filtered = filtered.filter(item => item.turnover_rate > 12);
            break;
          case 'medium':
            filtered = filtered.filter(item => item.turnover_rate >= 6 && item.turnover_rate <= 12);
            break;
          case 'low':
            filtered = filtered.filter(item => item.turnover_rate >= 3 && item.turnover_rate < 6);
            break;
          case 'very_low':
            filtered = filtered.filter(item => item.turnover_rate < 3);
            break;
        }
      }

      return filtered;
    });

    // 方法定义
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    };

    const getMetricClass = (metric) => {
      if (metric.label === '平均周转率') {
        return metric.value >= metric.target ? 'good' : 'bad';
      } else if (metric.label === '平均周转天数' || metric.label === '库存周转资金' || metric.label === '低周转SKU占比') {
        return metric.value <= metric.target ? 'good' : 'bad';
      }
      return '';
    };

    const getTurnoverRateClass = (rate) => {
      if (rate >= 12) return 'turnover-high';
      if (rate >= 6) return 'turnover-medium';
      if (rate >= 3) return 'turnover-low';
      return 'turnover-very-low';
    };

    const getAbcClassType = (abcClass) => {
      switch (abcClass) {
        case 'A':
          return 'success';
        case 'B':
          return 'warning';
        case 'C':
          return 'info';
        default:
          return '';
      }
    };

    const initDistributionChart = () => {
      if (!distributionChartRef.value) return;
      
      const chart = echarts.init(distributionChartRef.value);
      
      // 周转率区间分布
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        legend: {
          data: ['SKU数量', '库存价值占比']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: [
          {
            type: 'category',
            data: ['<1', '1-3', '3-6', '6-9', '9-12', '12-15', '>15'],
            axisLabel: {
              interval: 0
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: 'SKU数量',
            position: 'left'
          },
          {
            type: 'value',
            name: '库存价值占比',
            position: 'right',
            axisLabel: {
              formatter: '{value}%'
            }
          }
        ],
        series: [
          {
            name: 'SKU数量',
            type: 'bar',
            data: [10, 15, 25, 40, 30, 20, 10]
          },
          {
            name: '库存价值占比',
            type: 'line',
            yAxisIndex: 1,
            data: [25, 20, 18, 15, 12, 6, 4],
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
              width: 3
            }
          }
        ]
      };
      
      chart.setOption(option);
    };

    const initScatterChart = () => {
      if (!scatterChartRef.value) return;
      
      const chart = echarts.init(scatterChartRef.value);
      
      // 生成模拟数据
      const data = [];
      for (let i = 0; i < 50; i++) {
        const turnoverRate = Math.random() * 20;
        const inventoryValue = Math.random() * 100000;
        const abcClass = turnoverRate > 12 ? 'A' : (turnoverRate > 6 ? 'B' : 'C');
        const symbolSize = Math.sqrt(inventoryValue) / 30;
        
        data.push({
          value: [turnoverRate, inventoryValue],
          name: `商品${i+1}`,
          symbolSize: symbolSize,
          category: abcClass
        });
      }
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            return `商品: ${params.data.name}<br/>周转率: ${params.data.value[0].toFixed(2)}<br/>库存价值: ${formatCurrency(params.data.value[1])}`;
          }
        },
        legend: {
          data: ['A类商品', 'B类商品', 'C类商品'],
          right: '10%'
        },
        grid: {
          left: '3%',
          right: '12%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '周转率',
          splitLine: {
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '库存价值(元)',
          splitLine: {
            lineStyle: {
              type: 'dashed'
            }
          },
          axisLabel: {
            formatter: function(value) {
              return value >= 10000 ? (value / 10000) + '万' : value;
            }
          }
        },
        series: [
          {
            name: 'A类商品',
            type: 'scatter',
            data: data.filter(item => item.category === 'A'),
            itemStyle: {
              color: '#67c23a'
            }
          },
          {
            name: 'B类商品',
            type: 'scatter',
            data: data.filter(item => item.category === 'B'),
            itemStyle: {
              color: '#e6a23c'
            }
          },
          {
            name: 'C类商品',
            type: 'scatter',
            data: data.filter(item => item.category === 'C'),
            itemStyle: {
              color: '#909399'
            }
          }
        ]
      };
      
      chart.setOption(option);
    };

    const initTrendChart = () => {
      if (!trendChartRef.value) return;
      
      const chart = echarts.init(trendChartRef.value);
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['整体周转率', 'A类商品', 'B类商品', 'C类商品']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        },
        yAxis: {
          type: 'value',
          name: '周转率'
        },
        series: [
          {
            name: '整体周转率',
            type: 'line',
            stack: 'Total',
            data: [7.2, 7.5, 7.8, 8.0, 8.2, 8.4, 8.5, 8.7, 8.9, 9.1, 9.3, 9.5],
            lineStyle: {
              width: 3
            },
            symbol: 'circle',
            symbolSize: 8
          },
          {
            name: 'A类商品',
            type: 'line',
            stack: 'Total',
            data: [12.5, 12.8, 13.0, 13.2, 13.5, 13.8, 14.0, 14.2, 14.5, 14.8, 15.0, 15.2]
          },
          {
            name: 'B类商品',
            type: 'line',
            stack: 'Total',
            data: [8.0, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2]
          },
          {
            name: 'C类商品',
            type: 'line',
            stack: 'Total',
            data: [3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.3]
          }
        ]
      };
      
      chart.setOption(option);
    };

    // 生命周期钩子
    onMounted(() => {
      initDistributionChart();
      initScatterChart();
      initTrendChart();
    });

    // 监听器
    watch([timeRange, categoryFilter], () => {
      loading.value = true;
      // 模拟加载数据
      setTimeout(() => {
        initDistributionChart();
        initScatterChart();
        initTrendChart();
        loading.value = false;
      }, 800);
    });

    // 事件处理方法
    const refreshData = () => {
      loading.value = true;
      setTimeout(() => {
        initDistributionChart();
        initScatterChart();
        initTrendChart();
        loading.value = false;
        ElMessage.success('数据已更新');
      }, 800);
    };

    const exportData = () => {
      ElMessage.success('数据导出成功');
    };

    const handleSizeChange = (val) => {
      pageSize.value = val;
      // 重新加载数据
    };

    const handleCurrentChange = (val) => {
      currentPage.value = val;
      // 重新加载数据
    };

    return {
      loading,
      timeRange,
      categoryFilter,
      turnoverFilter,
      searchQuery,
      distributionChartRef,
      scatterChartRef,
      trendChartRef,
      currentPage,
      pageSize,
      totalItems,
      categories,
      turnoverMetrics,
      productList,
      filteredProductList,
      formatCurrency,
      getMetricClass,
      getTurnoverRateClass,
      getAbcClassType,
      refreshData,
      exportData,
      handleSizeChange,
      handleCurrentChange
    };
  }
};
</script>

<style scoped>
.turnover-analysis {
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

.turnover-overview {
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

.turnover-charts {
  margin-bottom: 30px;
}

.chart-container {
  margin-bottom: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.distribution-chart,
.scatter-chart,
.trend-chart {
  height: 350px;
  width: 100%;
}

.turnover-trend {
  margin-bottom: 30px;
}

.turnover-details {
  margin-top: 30px;
}

.table-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
  display: inline-block;
}

.table-actions {
  float: right;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.turnover-high {
  color: #67c23a;
  font-weight: bold;
}

.turnover-medium {
  color: #409eff;
  font-weight: bold;
}

.turnover-low {
  color: #e6a23c;
  font-weight: bold;
}

.turnover-very-low {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>