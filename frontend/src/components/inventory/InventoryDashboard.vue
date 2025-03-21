# frontend/src/components/inventory/InventoryDashboard.vue
<template>
  <div class="inventory-dashboard">
    <el-row :gutter="20">
      <!-- 库存概览卡片 -->
      <el-col :span="24">
        <el-card class="overview-card">
          <template #header>
            <div class="card-header">
              <span>库存概览</span>
              <div class="header-actions">
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
          <el-row :gutter="20">
            <el-col :span="6" v-for="metric in inventoryMetrics" :key="metric.label">
              <el-card :body-style="{ padding: '20px' }" shadow="hover">
                <div class="metric-item">
                  <div class="metric-value" :class="metric.trend">
                    {{ formatNumber(metric.value) }}
                    <el-icon v-if="metric.trend === 'up'"><CaretTop /></el-icon>
                    <el-icon v-else-if="metric.trend === 'down'"><CaretBottom /></el-icon>
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
        </el-card>
      </el-col>

      <!-- 库存预警区域 -->
      <el-col :span="12">
        <el-card class="warning-card">
          <template #header>
            <div class="card-header">
              <span>库存预警</span>
              <el-tag 
                v-if="warningCount > 0" 
                type="danger" 
                effect="dark"
              >
                {{ warningCount }}个预警
              </el-tag>
            </div>
          </template>
          <div class="warning-list">
            <el-table
              :data="warningItems"
              style="width: 100%"
              :max-height="400"
              v-loading="loading"
            >
              <el-table-column prop="product_code" label="商品编码" width="120" />
              <el-table-column prop="product_name" label="商品名称" width="150" />
              <el-table-column prop="warning_type" label="预警类型" width="100">
                <template #default="{ row }">
                  <el-tag
                    :type="getWarningTypeTag(row.warning_type)"
                    effect="plain"
                  >
                    {{ row.warning_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="current_stock" label="当前库存" width="100">
                <template #default="{ row }">
                  <span :class="{ 'text-danger': row.warning_type === '低库存' }">
                    {{ row.current_stock }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="threshold" label="预警阈值" width="100" />
              <el-table-column prop="suggested_action" label="建议操作" />
            </el-table>
          </div>
        </el-card>
      </el-col>

      <!-- 库存趋势图 -->
      <el-col :span="12">
        <el-card class="trend-card">
          <template #header>
            <div class="card-header">
              <span>库存趋势</span>
              <div class="header-actions">
                <el-select v-model="trendTimeRange" size="small">
                  <el-option label="最近7天" value="7" />
                  <el-option label="最近30天" value="30" />
                  <el-option label="最近90天" value="90" />
                </el-select>
              </div>
            </div>
          </template>
          <div class="trend-chart" ref="trendChartRef"></div>
        </el-card>
      </el-col>

      <!-- 库存分布图 -->
      <el-col :span="12">
        <el-card class="distribution-card">
          <template #header>
            <div class="card-header">
              <span>库存分布</span>
              <div class="header-actions">
                <el-radio-group v-model="distributionView" size="small">
                  <el-radio-button label="category">按分类</el-radio-button>
                  <el-radio-button label="location">按库位</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <div class="distribution-chart" ref="distributionChartRef"></div>
        </el-card>
      </el-col>

      <!-- 库存详情表格 -->
      <el-col :span="24">
        <el-card class="details-card">
          <template #header>
            <div class="card-header">
              <span>库存明细</span>
              <div class="header-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索商品..."
                  prefix-icon="Search"
                  clearable
                  size="small"
                  style="width: 200px; margin-right: 10px;"
                />
                <el-select
                  v-model="categoryFilter"
                  placeholder="商品分类"
                  clearable
                  size="small"
                  style="width: 150px; margin-right: 10px;"
                >
                  <el-option
                    v-for="category in categories"
                    :key="category.value"
                    :label="category.label"
                    :value="category.value"
                  />
                </el-select>
                <el-button-group>
                  <el-button size="small" @click="refreshDetails">
                    <el-icon><Refresh /></el-icon>
                  </el-button>
                  <el-button size="small" @click="exportDetails">
                    <el-icon><Download /></el-icon>
                  </el-button>
                </el-button-group>
              </div>
            </div>
          </template>
          <el-table
            :data="filteredInventoryDetails"
            style="width: 100%"
            :max-height="500"
            v-loading="detailsLoading"
          >
            <el-table-column prop="product_code" label="商品编码" width="120" sortable />
            <el-table-column prop="product_name" label="商品名称" width="150" sortable />
            <el-table-column prop="category" label="分类" width="100" sortable />
            <el-table-column prop="current_stock" label="当前库存" width="100" sortable>
              <template #default="{ row }">
                <span :class="{ 'stock-warning': isStockWarning(row) }">
                  {{ row.current_stock }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="min_stock" label="最低库存" width="100" />
            <el-table-column prop="max_stock" label="最高库存" width="100" />
            <el-table-column prop="last_update" label="最后更新" width="160" sortable />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="viewDetails(row)">
                    详情
                  </el-button>
                  <el-button size="small" type="primary" @click="createReplenishment(row)">
                    补货
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
      </el-col>
    </el-row>

    <!-- 商品详情对话框 -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="商品详情"
      width="60%"
    >
      <div v-if="selectedProduct">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="商品编码">{{ selectedProduct.product_code }}</el-descriptions-item>
          <el-descriptions-item label="商品名称">{{ selectedProduct.product_name }}</el-descriptions-item>
          <el-descriptions-item label="商品分类">{{ selectedProduct.category }}</el-descriptions-item>
          <el-descriptions-item label="当前库存">{{ selectedProduct.current_stock }}</el-descriptions-item>
          <el-descriptions-item label="最低库存">{{ selectedProduct.min_stock }}</el-descriptions-item>
          <el-descriptions-item label="最高库存">{{ selectedProduct.max_stock }}</el-descriptions-item>
          <el-descriptions-item label="库存状态">
            <el-tag :type="getStatusType(selectedProduct.status)">
              {{ selectedProduct.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">{{ selectedProduct.last_update }}</el-descriptions-item>
        </el-descriptions>

        <div class="stock-history-chart" ref="stockHistoryChartRef"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { CaretTop, CaretBottom, Refresh, Download, Search } from '@element-plus/icons-vue';

export default {
  name: 'InventoryDashboard',
  components: {
    CaretTop,
    CaretBottom,
    Refresh,
    Download,
    Search
  },
  setup() {
    // 状态定义
    const loading = ref(false);
    const detailsLoading = ref(false);
    const trendChartRef = ref(null);
    const distributionChartRef = ref(null);
    const stockHistoryChartRef = ref(null);
    const trendTimeRange = ref('7');
    const distributionView = ref('category');
    const searchQuery = ref('');
    const categoryFilter = ref('');
    const currentPage = ref(1);
    const pageSize = ref(20);
    const totalItems = ref(0);
    const detailsDialogVisible = ref(false);
    const selectedProduct = ref(null);

    // 模拟数据
    const inventoryMetrics = ref([
      {
        label: '总库存量',
        value: 12500,
        trend: 'up',
        change: 5.2
      },
      {
        label: '低库存SKU',
        value: 28,
        trend: 'down',
        change: -12.5
      },
      {
        label: '过量库存SKU',
        value: 15,
        trend: 'up',
        change: 8.3
      },
      {
        label: '正常库存SKU',
        value: 357,
        trend: 'up',
        change: 2.1
      }
    ]);

    const warningItems = ref([
      {
        product_code: 'SKU001',
        product_name: '商品A',
        warning_type: '低库存',
        current_stock: 5,
        threshold: 10,
        suggested_action: '建议补货20件'
      },
      {
        product_code: 'SKU002',
        product_name: '商品B',
        warning_type: '过量库存',
        current_stock: 200,
        threshold: 150,
        suggested_action: '建议停止补货'
      }
    ]);

    const categories = ref([
      { value: 'food', label: '食品' },
      { value: 'drink', label: '饮料' },
      { value: 'daily', label: '日用品' }
    ]);

    const inventoryDetails = ref([
      {
        product_code: 'SKU001',
        product_name: '商品A',
        category: '食品',
        current_stock: 5,
        min_stock: 10,
        max_stock: 100,
        last_update: '2024-03-21 10:00:00',
        status: '低库存'
      }
    ]);

    // 计算属性
    const warningCount = computed(() => warningItems.value.length);

    const filteredInventoryDetails = computed(() => {
      let filtered = [...inventoryDetails.value];
      
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

      return filtered;
    });

    // 方法定义
    const formatNumber = (num) => {
      return new Intl.NumberFormat().format(num);
    };

    const getWarningTypeTag = (type) => {
      switch (type) {
        case '低库存':
          return 'danger';
        case '过量库存':
          return 'warning';
        default:
          return 'info';
      }
    };

    const getStatusType = (status) => {
      switch (status) {
        case '低库存':
          return 'danger';
        case '过量库存':
          return 'warning';
        case '正常':
          return 'success';
        default:
          return 'info';
      }
    };

    const isStockWarning = (row) => {
      return row.current_stock < row.min_stock || row.current_stock > row.max_stock;
    };

    const initTrendChart = () => {
      if (!trendChartRef.value) return;
      
      const chart = echarts.init(trendChartRef.value);
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['库存量', '安全库存']
        },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '库存量',
            type: 'line',
            data: [120, 132, 101, 134, 90, 230, 210]
          },
          {
            name: '安全库存',
            type: 'line',
            data: [100, 100, 100, 100, 100, 100, 100],
            lineStyle: {
              type: 'dashed'
            }
          }
        ]
      };
      chart.setOption(option);
    };

    const initDistributionChart = () => {
      if (!distributionChartRef.value) return;
      
      const chart = echarts.init(distributionChartRef.value);
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
              show: false,
              position: 'center'
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
              { value: 1048, name: '食品' },
              { value: 735, name: '饮料' },
              { value: 580, name: '日用品' }
            ]
          }
        ]
      };
      chart.setOption(option);
    };

    // 生命周期钩子
    onMounted(() => {
      initTrendChart();
      initDistributionChart();
    });

    // 监听器
    watch(trendTimeRange, () => {
      // 更新趋势图数据
      initTrendChart();
    });

    watch(distributionView, () => {
      // 更新分布图数据
      initDistributionChart();
    });

    // 事件处理方法
    const refreshData = () => {
      ElMessage.success('数据已更新');
    };

    const exportData = () => {
      ElMessage.success('导出成功');
    };

    const refreshDetails = () => {
      detailsLoading.value = true;
      setTimeout(() => {
        detailsLoading.value = false;
        ElMessage.success('数据已更新');
      }, 1000);
    };

    const exportDetails = () => {
      ElMessage.success('导出成功');
    };

    const handleSizeChange = (val) => {
      pageSize.value = val;
      // 重新加载数据
    };

    const handleCurrentChange = (val) => {
      currentPage.value = val;
      // 重新加载数据
    };

    const viewDetails = (row) => {
      selectedProduct.value = row;
      detailsDialogVisible.value = true;
      // 在对话框打开后初始化库存历史图表
      setTimeout(() => {
        if (stockHistoryChartRef.value) {
          const chart = echarts.init(stockHistoryChartRef.value);
          const option = {
            tooltip: {
              trigger: 'axis'
            },
            xAxis: {
              type: 'category',
              data: ['1月', '2月', '3月', '4月', '5月', '6月']
            },
            yAxis: {
              type: 'value'
            },
            series: [
              {
                data: [150, 230, 224, 218, 135, 147],
                type: 'line',
                smooth: true
              }
            ]
          };
          chart.setOption(option);
        }
      }, 100);
    };

    const createReplenishment = (row) => {
      ElMessage.success(`已为${row.product_name}创建补货单`);
    };

    return {
      loading,
      detailsLoading,
      trendChartRef,
      distributionChartRef,
      stockHistoryChartRef,
      trendTimeRange,
      distributionView,
      searchQuery,
      categoryFilter,
      currentPage,
      pageSize,
      totalItems,
      detailsDialogVisible,
      selectedProduct,
      inventoryMetrics,
      warningItems,
      warningCount,
      categories,
      inventoryDetails,
      filteredInventoryDetails,
      formatNumber,
      getWarningTypeTag,
      getStatusType,
      isStockWarning,
      refreshData,
      exportData,
      refreshDetails,
      exportDetails,
      handleSizeChange,
      handleCurrentChange,
      viewDetails,
      createReplenishment
    };
  }
};
</script>

<style scoped>
.inventory-dashboard {
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
  gap: 10px;
}

.metric-item {
  text-align: center;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.metric-value.up {
  color: #67c23a;
}

.metric-value.down {
  color: #f56c6c;
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

.warning-list {
  margin-top: 10px;
}

.trend-chart,
.distribution-chart {
  height: 300px;
  width: 100%;
}

.stock-history-chart {
  height: 300px;
  width: 100%;
  margin-top: 20px;
}

.text-danger {
  color: #f56c6c;
}

.stock-warning {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-card) {
  margin-bottom: 20px;
}

:deep(.el-table .cell) {
  white-space: nowrap;
}
</style>