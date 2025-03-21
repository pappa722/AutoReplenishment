&lt;template>
  &lt;div class="sales-trend-chart">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="chart-header">
          &lt;span>{{ title }}&lt;/span>
          &lt;div class="chart-controls">
            &lt;el-select
              v-model="selectedTimeRange"
              placeholder="时间范围"
              size="small"
              @change="handleTimeRangeChange"
            >
              &lt;el-option
                v-for="item in timeRangeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            &lt;/el-select>
            &lt;el-select
              v-model="selectedMetric"
              placeholder="指标"
              size="small"
              @change="handleMetricChange"
            >
              &lt;el-option
                v-for="item in metricOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            &lt;/el-select>
          &lt;/div>
        &lt;/div>
      &lt;/template>

      &lt;div class="chart-container" ref="chartContainer">
        &lt;div v-if="loading" class="chart-loading">
          &lt;el-skeleton animated :rows="8" />
        &lt;/div>
        &lt;div v-else-if="error" class="chart-error">
          &lt;el-empty
            description="加载数据失败"
            :image-size="100"
          >
            &lt;template #description>
              &lt;p>{{ error }}&lt;/p>
            &lt;/template>
            &lt;el-button @click="fetchData">重试&lt;/el-button>
          &lt;/el-empty>
        &lt;/div>
        &lt;div v-else-if="!hasData" class="chart-empty">
          &lt;el-empty description="暂无数据" :image-size="100">
            &lt;el-button @click="fetchData">刷新&lt;/el-button>
          &lt;/el-empty>
        &lt;/div>
        &lt;div v-else class="chart-content" ref="chartDom">&lt;/div>
      &lt;/div>

      &lt;div class="chart-footer" v-if="hasData && !loading">
        &lt;div class="chart-summary">
          &lt;div class="summary-item">
            &lt;div class="summary-label">总{{ metricLabel }}</div>
            &lt;div class="summary-value">{{ formatValue(totalValue) }}</div>
          &lt;/div>
          &lt;div class="summary-item">
            &lt;div class="summary-label">平均{{ metricLabel }}</div>
            &lt;div class="summary-value">{{ formatValue(avgValue) }}</div>
          &lt;/div>
          &lt;div class="summary-item">
            &lt;div class="summary-label">环比</div>
            &lt;div class="summary-value" :class="growthClass">
              {{ formatGrowth(growth) }}
            &lt;/div>
          &lt;/div>
        &lt;/div>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent,
  LineChart,
  CanvasRenderer
]);

export default {
  name: 'SalesTrendChart',
  props: {
    title: {
      type: String,
      default: '销售趋势'
    },
    apiUrl: {
      type: String,
      required: true
    },
    defaultTimeRange: {
      type: String,
      default: 'last30days'
    },
    defaultMetric: {
      type: String,
      default: 'sales_amount'
    },
    height: {
      type: String,
      default: '400px'
    }
  },
  setup(props) {
    // 图表实例
    let chartInstance = null;
    const chartDom = ref(null);
    const chartContainer = ref(null);
    
    // 状态
    const loading = ref(false);
    const error = ref(null);
    const chartData = ref([]);
    
    // 选项
    const selectedTimeRange = ref(props.defaultTimeRange);
    const selectedMetric = ref(props.defaultMetric);
    
    // 时间范围选项
    const timeRangeOptions = [
      { label: '最近7天', value: 'last7days' },
      { label: '最近30天', value: 'last30days' },
      { label: '最近90天', value: 'last90days' },
      { label: '本月', value: 'thisMonth' },
      { label: '上月', value: 'lastMonth' },
      { label: '本季度', value: 'thisQuarter' },
      { label: '上季度', value: 'lastQuarter' },
      { label: '今年', value: 'thisYear' },
      { label: '去年', value: 'lastYear' }
    ];
    
    // 指标选项
    const metricOptions = [
      { label: '销售额', value: 'sales_amount' },
      { label: '销售数量', value: 'sales_quantity' },
      { label: '订单数', value: 'order_count' },
      { label: '平均客单价', value: 'average_order_value' }
    ];
    
    // 计算属性
    const hasData = computed(() => chartData.value && chartData.value.length > 0);
    
    const metricLabel = computed(() => {
      const option = metricOptions.find(opt => opt.value === selectedMetric.value);
      return option ? option.label : '';
    });
    
    const totalValue = computed(() => {
      if (!hasData.value) return 0;
      return chartData.value.reduce((sum, item) => sum + item.value, 0);
    });
    
    const avgValue = computed(() => {
      if (!hasData.value) return 0;
      return totalValue.value / chartData.value.length;
    });
    
    const growth = computed(() => {
      if (!hasData.value || chartData.value.length < 2) return 0;
      
      // 简单计算：当前周期与上一周期的比较
      const currentPeriodData = [...chartData.value];
      const dataLength = currentPeriodData.length;
      const halfLength = Math.floor(dataLength / 2);
      
      const currentPeriod = currentPeriodData.slice(halfLength);
      const previousPeriod = currentPeriodData.slice(0, halfLength);
      
      const currentSum = currentPeriod.reduce((sum, item) => sum + item.value, 0);
      const previousSum = previousPeriod.reduce((sum, item) => sum + item.value, 0);
      
      if (previousSum === 0) return 0;
      return (currentSum - previousSum) / previousSum;
    });
    
    const growthClass = computed(() => {
      if (growth.value > 0) return 'positive';
      if (growth.value < 0) return 'negative';
      return '';
    });
    
    // 方法
    const initChart = () => {
      if (chartInstance) {
        chartInstance.dispose();
      }
      
      if (!chartDom.value) return;
      
      chartInstance = echarts.init(chartDom.value);
      chartInstance.setOption({
        grid: {
          left: '3%',
          right: '4%',
          bottom: '10%',
          top: '8%',
          containLabel: true
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: function(params) {
            const param = params[0];
            return `${param.axisValue}<br/>${metricLabel.value}: ${formatValue(param.value)}`;
          }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: [],
          axisLabel: {
            formatter: function(value) {
              // 根据时间范围调整日期显示格式
              if (selectedTimeRange.value.includes('day')) {
                return value.substring(5); // 只显示月-日
              }
              return value;
            }
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            formatter: function(value) {
              return formatValue(value, true);
            }
          }
        },
        series: [
          {
            name: metricLabel.value,
            type: 'line',
            stack: 'Total',
            data: [],
            areaStyle: {
              opacity: 0.3
            },
            lineStyle: {
              width: 2
            },
            symbol: 'circle',
            symbolSize: 6,
            emphasis: {
              focus: 'series',
              itemStyle: {
                borderWidth: 2
              }
            }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100
          },
          {
            start: 0,
            end: 100
          }
        ],
        color: ['#409EFF']
      });
      
      window.addEventListener('resize', handleResize);
    };
    
    const updateChart = () => {
      if (!chartInstance || !hasData.value) return;
      
      const xAxisData = chartData.value.map(item => item.date);
      const seriesData = chartData.value.map(item => item.value);
      
      chartInstance.setOption({
        xAxis: {
          data: xAxisData
        },
        series: [
          {
            name: metricLabel.value,
            data: seriesData
          }
        ]
      });
    };
    
    const handleResize = () => {
      chartInstance && chartInstance.resize();
    };
    
    const fetchData = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        // 构建API请求参数
        const params = {
          timeRange: selectedTimeRange.value,
          metric: selectedMetric.value
        };
        
        // 模拟API请求
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟数据
        const today = new Date();
        const data = [];
        
        let daysCount = 30;
        if (selectedTimeRange.value === 'last7days') daysCount = 7;
        if (selectedTimeRange.value === 'last90days') daysCount = 90;
        
        for (let i = daysCount - 1; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          
          // 格式化日期为 YYYY-MM-DD
          const formattedDate = date.toISOString().split('T')[0];
          
          // 生成随机值，根据指标类型调整范围
          let value;
          if (selectedMetric.value === 'sales_amount') {
            value = Math.floor(Math.random() * 10000) + 5000;
          } else if (selectedMetric.value === 'sales_quantity') {
            value = Math.floor(Math.random() * 100) + 50;
          } else if (selectedMetric.value === 'order_count') {
            value = Math.floor(Math.random() * 50) + 10;
          } else {
            value = Math.floor(Math.random() * 200) + 100;
          }
          
          // 添加一些趋势
          value = value * (1 + i * 0.01);
          
          // 添加周末效应
          const dayOfWeek = date.getDay();
          if (dayOfWeek === 0 || dayOfWeek === 6) {
            value = value * 1.2; // 周末销售额增加
          }
          
          data.push({
            date: formattedDate,
            value: value
          });
        }
        
        chartData.value = data;
      } catch (err) {
        console.error('Failed to fetch chart data:', err);
        error.value = '获取数据失败，请稍后重试';
      } finally {
        loading.value = false;
        
        // 确保DOM已更新后再初始化或更新图表
        nextTick(() => {
          if (!chartInstance) {
            initChart();
          }
          updateChart();
        });
      }
    };
    
    const handleTimeRangeChange = () => {
      fetchData();
    };
    
    const handleMetricChange = () => {
      fetchData();
    };
    
    const formatValue = (value, compact = false) => {
      if (value === null || value === undefined) return '-';
      
      if (selectedMetric.value === 'sales_amount' || selectedMetric.value === 'average_order_value') {
        if (compact && value >= 10000) {
          return '¥' + (value / 10000).toFixed(1) + '万';
        }
        return '¥' + value.toFixed(2);
      } else {
        if (compact && value >= 10000) {
          return (value / 10000).toFixed(1) + '万';
        }
        return value.toFixed(0);
      }
    };
    
    const formatGrowth = (value) => {
      if (value === null || value === undefined) return '-';
      const sign = value > 0 ? '+' : '';
      return sign + (value * 100).toFixed(2) + '%';
    };
    
    // 生命周期钩子
    onMounted(() => {
      fetchData();
    });
    
    onUnmounted(() => {
      if (chartInstance) {
        chartInstance.dispose();
        chartInstance = null;
      }
      window.removeEventListener('resize', handleResize);
    });
    
    // 监听props变化
    watch(() => props.apiUrl, fetchData);
    
    return {
      chartDom,
      chartContainer,
      loading,
      error,
      chartData,
      selectedTimeRange,
      selectedMetric,
      timeRangeOptions,
      metricOptions,
      hasData,
      metricLabel,
      totalValue,
      avgValue,
      growth,
      growthClass,
      fetchData,
      handleTimeRangeChange,
      handleMetricChange,
      formatValue,
      formatGrowth
    };
  }
};
&lt;/script>

&lt;style scoped>
.sales-trend-chart {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 10px;
}

.chart-container {
  position: relative;
  width: 100%;
  height: v-bind('props.height');
}

.chart-content {
  width: 100%;
  height: 100%;
}

.chart-loading,
.chart-error,
.chart-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.chart-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.chart-summary {
  display: flex;
  justify-content: space-around;
}

.summary-item {
  text-align: center;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.summary-value.positive {
  color: #67C23A;
}

.summary-value.negative {
  color: #F56C6C;
}
&lt;/style>