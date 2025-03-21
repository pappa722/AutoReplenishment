# frontend/src/components/inventory/AbcAnalysis.vue
<template>
  <div class="abc-analysis">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>ABC分类分析</span>
          <div class="header-actions">
            <el-select v-model="analysisType" size="small" style="width: 150px; margin-right: 10px;">
              <el-option label="按销售额" value="revenue" />
              <el-option label="按销售量" value="quantity" />
              <el-option label="按利润率" value="profit" />
            </el-select>
            <el-select v-model="timeRange" size="small" style="width: 150px; margin-right: 10px;">
              <el-option label="最近30天" value="30" />
              <el-option label="最近90天" value="90" />
              <el-option label="最近180天" value="180" />
              <el-option label="最近365天" value="365" />
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
      
      <div class="analysis-summary">
        <el-row :gutter="20">
          <el-col :span="8" v-for="category in categories" :key="category.type">
            <el-card shadow="hover" :body-style="{ padding: '15px' }">
              <div class="category-summary">
                <div class="category-header">
                  <div class="category-type" :class="category.type">
                    {{ category.type }}类
                  </div>
                  <div class="category-count">
                    {{ category.count }}个SKU
                  </div>
                </div>
                <div class="category-metrics">
                  <div class="metric">
                    <div class="metric-label">销售额占比</div>
                    <div class="metric-value">{{ category.revenue }}%</div>
                  </div>
                  <div class="metric">
                    <div class="metric-label">SKU占比</div>
                    <div class="metric-value">{{ category.sku }}%</div>
                  </div>
                  <div class="metric">
                    <div class="metric-label">库存占比</div>
                    <div class="metric-value">{{ category.inventory }}%</div>
                  </div>
                </div>
                <div class="category-suggestion">
                  <strong>管理建议：</strong> {{ category.suggestion }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <div class="analysis-charts">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-container">
              <div class="chart-title">帕累托分析图</div>
              <div class="pareto-chart" ref="paretoChartRef"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-container">
              <div class="chart-title">ABC分类占比</div>
              <div class="pie-chart" ref="pieChartRef"></div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <div class="analysis-table">
        <div class="table-title">商品分类明细</div>
        <el-table
          :data="productList"
          style="width: 100%"
          :max-height="400"
          v-loading="loading"
        >
          <el-table-column prop="product_code" label="商品编码" width="120" sortable />
          <el-table-column prop="product_name" label="商品名称" width="150" sortable />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="abc_class" label="ABC分类" width="100">
            <template #default="{ row }">
              <el-tag :type="getClassType(row.abc_class)" effect="plain">
                {{ row.abc_class }}类
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="sales_revenue" label="销售额" width="120" sortable>
            <template #default="{ row }">
              {{ formatCurrency(row.sales_revenue) }}
            </template>
          </el-table-column>
          <el-table-column prop="sales_quantity" label="销售量" width="100" sortable />
          <el-table-column prop="profit_rate" label="利润率" width="100" sortable>
            <template #default="{ row }">
              {{ row.profit_rate }}%
            </template>
          </el-table-column>
          <el-table-column prop="revenue_percentage" label="销售额占比" width="120" sortable>
            <template #default="{ row }">
              <div class="percentage-bar">
                <div 
                  class="percentage-fill" 
                  :class="getClassColor(row.abc_class)" 
                  :style="{ width: row.revenue_percentage + '%' }"
                ></div>
                <span>{{ row.revenue_percentage }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="cumulative_percentage" label="累计占比" width="120" sortable>
            <template #default="{ row }">
              {{ row.cumulative_percentage }}%
            </template>
          </el-table-column>
          <el-table-column prop="current_stock" label="当前库存" width="100" sortable />
          <el-table-column prop="suggested_action" label="管理建议" />
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
import { ref, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { Refresh, Download } from '@element-plus/icons-vue';

export default {
  name: 'AbcAnalysis',
  components: {
    Refresh,
    Download
  },
  setup() {
    // 状态定义
    const loading = ref(false);
    const analysisType = ref('revenue');
    const timeRange = ref('90');
    const paretoChartRef = ref(null);
    const pieChartRef = ref(null);
    const currentPage = ref(1);
    const pageSize = ref(20);
    const totalItems = ref(100);

    // 模拟数据
    const categories = ref([
      {
        type: 'A',
        count: 50,
        revenue: 80,
        sku: 20,
        inventory: 30,
        suggestion: '重点管理，确保高可用性，优化库存水平，提高周转率'
      },
      {
        type: 'B',
        count: 75,
        revenue: 15,
        sku: 30,
        inventory: 35,
        suggestion: '定期监控，保持适度库存，优化订货批量和频率'
      },
      {
        type: 'C',
        count: 125,
        revenue: 5,
        sku: 50,
        inventory: 35,
        suggestion: '简化管理，降低库存水平，延长订货周期，考虑淘汰滞销品'
      }
    ]);

    const productList = ref([
      {
        product_code: 'SKU001',
        product_name: '高端牛奶',
        category: '饮料',
        abc_class: 'A',
        sales_revenue: 120000,
        sales_quantity: 5000,
        profit_rate: 25,
        revenue_percentage: 12.5,
        cumulative_percentage: 12.5,
        current_stock: 500,
        suggested_action: '保持高库存可用性，优化补货周期'
      },
      {
        product_code: 'SKU002',
        product_name: '巧克力饼干',
        category: '食品',
        abc_class: 'A',
        sales_revenue: 95000,
        sales_quantity: 8500,
        profit_rate: 22,
        revenue_percentage: 10.2,
        cumulative_percentage: 22.7,
        current_stock: 450,
        suggested_action: '密切监控销售趋势，优化库存水平'
      },
      {
        product_code: 'SKU003',
        product_name: '洗发水',
        category: '日用品',
        abc_class: 'B',
        sales_revenue: 45000,
        sales_quantity: 1500,
        profit_rate: 18,
        revenue_percentage: 4.8,
        cumulative_percentage: 27.5,
        current_stock: 300,
        suggested_action: '定期检查库存，适度降低安全库存'
      },
      {
        product_code: 'SKU004',
        product_name: '纸巾',
        category: '日用品',
        abc_class: 'C',
        sales_revenue: 12000,
        sales_quantity: 3000,
        profit_rate: 15,
        revenue_percentage: 1.3,
        cumulative_percentage: 28.8,
        current_stock: 800,
        suggested_action: '降低库存水平，延长订货周期'
      }
    ]);

    // 方法定义
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(value);
    };

    const getClassType = (abcClass) => {
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

    const getClassColor = (abcClass) => {
      switch (abcClass) {
        case 'A':
          return 'class-a';
        case 'B':
          return 'class-b';
        case 'C':
          return 'class-c';
        default:
          return '';
      }
    };

    const initParetoChart = () => {
      if (!paretoChartRef.value) return;
      
      const chart = echarts.init(paretoChartRef.value);
      
      // 模拟数据
      const data = productList.value.slice(0, 20).map(item => ({
        name: item.product_name,
        value: item.sales_revenue
      })).sort((a, b) => b.value - a.value);
      
      const names = data.map(item => item.name);
      const values = data.map(item => item.value);
      
      // 计算累计百分比
      const total = values.reduce((sum, val) => sum + val, 0);
      let cumulative = 0;
      const cumulativePercentage = values.map(val => {
        cumulative += val;
        return (cumulative / total * 100).toFixed(1);
      });
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function(params) {
            const barData = params[0];
            const lineData = params[1];
            return `${barData.name}<br/>${barData.seriesName}: ${formatCurrency(barData.value)}<br/>${lineData.seriesName}: ${lineData.value}%`;
          }
        },
        legend: {
          data: ['销售额', '累计占比']
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
            data: names,
            axisLabel: {
              interval: 0,
              rotate: 45
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '销售额',
            position: 'left'
          },
          {
            type: 'value',
            name: '累计占比',
            position: 'right',
            min: 0,
            max: 100,
            axisLabel: {
              formatter: '{value}%'
            }
          }
        ],
        series: [
          {
            name: '销售额',
            type: 'bar',
            data: values,
            itemStyle: {
              color: function(params) {
                if (params.dataIndex < Math.floor(names.length * 0.2)) {
                  return '#67c23a';  // A类
                } else if (params.dataIndex < Math.floor(names.length * 0.5)) {
                  return '#e6a23c';  // B类
                } else {
                  return '#909399';  // C类
                }
              }
            }
          },
          {
            name: '累计占比',
            type: 'line',
            yAxisIndex: 1,
            data: cumulativePercentage,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: {
              width: 3,
              color: '#409eff'
            },
            itemStyle: {
              color: '#409eff'
            }
          }
        ]
      };
      
      chart.setOption(option);
    };

    const initPieChart = () => {
      if (!pieChartRef.value) return;
      
      const chart = echarts.init(pieChartRef.value);
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          data: ['A类商品', 'B类商品', 'C类商品']
        },
        series: [
          {
            name: 'ABC分类',
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
              { value: 80, name: 'A类商品', itemStyle: { color: '#67c23a' } },
              { value: 15, name: 'B类商品', itemStyle: { color: '#e6a23c' } },
              { value: 5, name: 'C类商品', itemStyle: { color: '#909399' } }
            ]
          }
        ]
      };
      
      chart.setOption(option);
    };

    // 生命周期钩子
    onMounted(() => {
      initParetoChart();
      initPieChart();
    });

    // 监听器
    watch([analysisType, timeRange], () => {
      loading.value = true;
      // 模拟加载数据
      setTimeout(() => {
        initParetoChart();
        initPieChart();
        loading.value = false;
      }, 800);
    });

    // 事件处理方法
    const refreshData = () => {
      loading.value = true;
      setTimeout(() => {
        initParetoChart();
        initPieChart();
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
      analysisType,
      timeRange,
      paretoChartRef,
      pieChartRef,
      currentPage,
      pageSize,
      totalItems,
      categories,
      productList,
      formatCurrency,
      getClassType,
      getClassColor,
      refreshData,
      exportData,
      handleSizeChange,
      handleCurrentChange
    };
  }
};
</script>

<style scoped>
.abc-analysis {
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

.analysis-summary {
  margin-bottom: 30px;
}

.category-summary {
  padding: 10px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.category-type {
  font-size: 24px;
  font-weight: bold;
  padding: 5px 15px;
  border-radius: 4px;
}

.category-type.A {
  background-color: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.category-type.B {
  background-color: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.category-type.C {
  background-color: rgba(144, 147, 153, 0.2);
  color: #909399;
}

.category-count {
  font-size: 16px;
  color: #606266;
}

.category-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
}

.metric {
  text-align: center;
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.category-suggestion {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  border-top: 1px dashed #ebeef5;
  padding-top: 10px;
}

.analysis-charts {
  margin-bottom: 30px;
}

.chart-container {
  height: 400px;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.pareto-chart,
.pie-chart {
  height: 350px;
  width: 100%;
}

.table-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.percentage-bar {
  position: relative;
  width: 100%;
  height: 20px;
  background-color: #f5f7fa;
  border-radius: 10px;
  overflow: hidden;
}

.percentage-fill {
  position: absolute;
  height: 100%;
  left: 0;
  top: 0;
  border-radius: 10px;
}

.percentage-fill.class-a {
  background-color: rgba(103, 194, 58, 0.6);
}

.percentage-fill.class-b {
  background-color: rgba(230, 162, 60, 0.6);
}

.percentage-fill.class-c {
  background-color: rgba(144, 147, 153, 0.6);
}

.percentage-bar span {
  position: absolute;
  right: 10px;
  top: 0;
  line-height: 20px;
  font-size: 12px;
  color: #303133;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>