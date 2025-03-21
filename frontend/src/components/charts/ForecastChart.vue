&lt;template>
  &lt;div class="forecast-chart">
    &lt;div ref="chartContainer" :style="{ width: '100%', height: height + 'px' }">&lt;/div>
  &lt;/div>
&lt;/template>

&lt;script>
import * as echarts from 'echarts';
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';

export default {
  name: 'ForecastChart',
  props: {
    // 历史数据
    historicalData: {
      type: Array,
      required: true
    },
    // 预测数据
    forecastData: {
      type: Array,
      required: true
    },
    // 预测上限
    upperBound: {
      type: Array,
      default: () => []
    },
    // 预测下限
    lowerBound: {
      type: Array,
      default: () => []
    },
    // 图表高度
    height: {
      type: Number,
      default: 500
    },
    // 图表标题
    title: {
      type: String,
      default: '销量预测'
    },
    // 置信区间说明
    confidenceLevel: {
      type: String,
      default: '95%'
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
    const historicalData = ref([]);
    const forecastData = ref([]);
    const activeTab = ref('overview');
    
    // 选项
    const selectedModel = ref(props.defaultModel);
    const selectedMetric = ref(props.defaultMetric);
    const forecastPeriod = ref('30days');
    const showConfidenceInterval = ref(true);
    
    // 模型选项
    const modelOptions = [
      { label: 'SARIMA', value: 'sarima' },
      { label: 'Prophet', value: 'prophet' },
      { label: 'LSTM', value: 'lstm' },
      { label: '随机森林', value: 'random_forest' },
      { label: 'XGBoost', value: 'xgboost' }
    ];
    
    // 指标选项
    const metricOptions = [
      { label: '销售额', value: 'sales_amount' },
      { label: '销售数量', value: 'sales_quantity' },
      { label: '订单数', value: 'order_count' }
    ];
    
    // 预测周期选项
    const periodOptions = [
      { label: '未来7天', value: '7days' },
      { label: '未来30天', value: '30days' },
      { label: '未来90天', value: '90days' }
    ];
    
    // 计算属性
    const hasData = computed(() => 
      historicalData.value && historicalData.value.length > 0 && 
      forecastData.value && forecastData.value.length > 0
    );
    
    const metricLabel = computed(() => {
      const option = metricOptions.find(opt => opt.value === selectedMetric.value);
      return option ? option.label : '';
    });
    
    const selectedModelLabel = computed(() => {
      const option = modelOptions.find(opt => opt.value === selectedModel.value);
      return option ? option.label : '';
    });
    
    const forecastPeriodLabel = computed(() => {
      const option = periodOptions.find(opt => opt.value === forecastPeriod.value);
      return option ? option.label : '';
    });
    
    const forecastStats = computed(() => {
      if (!hasData.value) return {
        totalForecast: 0,
        growth: 0,
        accuracy: 0,
        confidenceLevel: 95,
        lastUpdated: '-',
        trainingPeriod: '-',
        metrics: {
          mae: 0,
          rmse: 0,
          mape: 0,
          r2: 0
        }
      };
      
      // 计算预测总量
      const totalForecast = forecastData.value.reduce((sum, item) => sum + item.forecast, 0);
      
      // 计算历史总量（用于计算环比）
      const historicalTotal = historicalData.value.slice(-forecastData.value.length).reduce((sum, item) => sum + item.value, 0);
      
      // 计算环比变化
      const growth = historicalTotal > 0 ? (totalForecast - historicalTotal) / historicalTotal : 0;
      
      return {
        totalForecast,
        growth,
        accuracy: 0.92, // 模拟数据
        confidenceLevel: 95,
        lastUpdated: new Date().toLocaleString(),
        trainingPeriod: '过去180天数据',
        metrics: {
          mae: totalForecast * 0.05, // 模拟数据
          rmse: totalForecast * 0.08, // 模拟数据
          mape: 0.07, // 模拟数据
          r2: 0.86 // 模拟数据
        }
      };
    });
    
    const forecastDetails = computed(() => {
      return forecastData.value.map(item => ({
        date: item.date,
        forecast: item.forecast,
        lower: item.lower,
        upper: item.upper
      }));
    });
    
    // 初始化图表
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
          top: '30px',
          containLabel: true
        },
        legend: {
          data: ['历史数据', '预测数据', '置信区间'],
          top: 0
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          formatter: function(params) {
            let result = params[0].axisValue + '<br/>';
            
            params.forEach(param => {
              if (param.seriesName === '历史数据') {
                result += `${param.seriesName}: ${formatValue(param.value)}<br/>`;
              } else if (param.seriesName === '预测数据') {
                result += `${param.seriesName}: ${formatValue(param.value)}<br/>`;
                
                // 查找对应日期的置信区间
                const forecastItem = forecastData.value.find(item => item.date === param.axisValue);
                if (forecastItem) {
                  result += `置信区间: ${formatValue(forecastItem.lower)} ~ ${formatValue(forecastItem.upper)}<br/>`;
                }
              }
            });
            
            return result;
          }
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: []
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
            name: '历史数据',
            type: 'line',
            data: [],
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2
            }
          },
          {
            name: '预测数据',
            type: 'line',
            data: [],
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dashed'
            }
          },
          {
            name: '置信区间',
            type: 'line',
            data: [],
            lineStyle: { opacity: 0 },
            areaStyle: {
              opacity: 0.2
            },
            tooltip: {
              show: false
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
        color: ['#409EFF', '#67C23A', '#E6A23C']
      });
      
      window.addEventListener('resize', handleResize);
    };

    const updateChart = () => {
      if (!chartInstance || !hasData.value) return;
      
      // 合并历史数据和预测数据的日期
      const allDates = [
        ...historicalData.value.map(item => item.date),
        ...forecastData.value.map(item => item.date)
      ];
      
      // 准备历史数据系列
      const historicalSeries = allDates.map(date => {
        const item = historicalData.value.find(d => d.date === date);
        return item ? item.value : '-';
      });
      
      // 准备预测数据系列
      const forecastSeries = allDates.map(date => {
        const item = forecastData.value.find(d => d.date === date);
        return item ? item.forecast : '-';
      });
      
      // 准备置信区间数据
      const confidenceAreaData = showConfidenceInterval.value ? allDates.map(date => {
        const item = forecastData.value.find(d => d.date === date);
        return item ? [item.lower, item.upper] : '-';
      }) : [];
      
      // 更新图表选项
      chartInstance.setOption({
        xAxis: {
          data: allDates
        },
        series: [
          {
            name: '历史数据',
            data: historicalSeries
          },
          {
            name: '预测数据',
            data: forecastSeries
          },
          {
            name: '置信区间',
            data: confidenceAreaData,
            areaStyle: {
              opacity: showConfidenceInterval.value ? 0.2 : 0
            }
          }
        ]
      });
      
      // 添加标记线，分隔历史数据和预测数据
      if (historicalData.value.length > 0) {
        const lastHistoricalDate = historicalData.value[historicalData.value.length - 1].date;
        chartInstance.setOption({
          series: [
            {
              name: '历史数据',
              markLine: {
                silent: true,
                lineStyle: {
                  color: '#409EFF',
                  type: 'dashed'
                },
                data: [
                  {
                    xAxis: lastHistoricalDate,
                    label: {
                      formatter: '当前',
                      position: 'start'
                    }
                  }
                ]
              }
            }
          ]
        });
      }
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
          model: selectedModel.value,
          metric: selectedMetric.value,
          period: forecastPeriod.value
        };
        
        // 模拟API请求
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟数据
        // 1. 历史数据
        const today = new Date();
        const historical = [];
        
        // 生成过去60天的历史数据
        for (let i = 59; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          const formattedDate = date.toISOString().split('T')[0];
          
          // 生成基础值
          let baseValue;
          if (selectedMetric.value === 'sales_amount') {
            baseValue = Math.floor(Math.random() * 10000) + 5000;
          } else if (selectedMetric.value === 'sales_quantity') {
            baseValue = Math.floor(Math.random() * 100) + 50;
          } else {
            baseValue = Math.floor(Math.random() * 50) + 10;
          }
          
          // 添加趋势
          baseValue = baseValue * (1 + i * 0.005);
          
          // 添加周末效应
          const dayOfWeek = date.getDay();
          if (dayOfWeek === 0 || dayOfWeek === 6) {
            baseValue = baseValue * 1.2;
          }
          
          // 添加一些随机波动
          const noise = (Math.random() - 0.5) * 0.1;
          baseValue = baseValue * (1 + noise);
          
          historical.push({
            date: formattedDate,
            value: baseValue
          });
        }
        
        // 2. 预测数据
        const forecast = [];
        let forecastDays = 30;
        if (forecastPeriod.value === '7days') forecastDays = 7;
        if (forecastPeriod.value === '90days') forecastDays = 90;
        
        // 基于历史数据的最后一个值作为起点
        const lastHistoricalValue = historical[historical.length - 1].value;
        
        // 生成预测数据
        for (let i = 1; i <= forecastDays; i++) {
          const date = new Date(today);
          date.setDate(date.getDate() + i);
          const formattedDate = date.toISOString().split('T')[0];
          
          // 生成预测值，添加趋势和一些随机波动
          let forecastValue = lastHistoricalValue * (1 + i * 0.01);
          const noise = (Math.random() - 0.5) * 0.05;
          forecastValue = forecastValue * (1 + noise);
          
          // 添加周末效应
          const dayOfWeek = date.getDay();
          if (dayOfWeek === 0 || dayOfWeek === 6) {
            forecastValue = forecastValue * 1.2;
          }
          
          // 计算置信区间
          const lowerBound = forecastValue * (1 - 0.1 - i * 0.005); // 随着时间增加，不确定性增加
          const upperBound = forecastValue * (1 + 0.1 + i * 0.005);
          
          forecast.push({
            date: formattedDate,
            forecast: forecastValue,
            lower: lowerBound,
            upper: upperBound
          });
        }
        
        historicalData.value = historical;
        forecastData.value = forecast;
      } catch (err) {
        console.error('Failed to fetch forecast data:', err);
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
    
    const handleModelChange = () => {
      fetchData();
    };
    
    const handleMetricChange = () => {
      fetchData();
    };
    
    const handlePeriodChange = () => {
      fetchData();
    };
    
    const toggleConfidenceInterval = () => {
      updateChart();
    };
    
    const formatValue = (value, compact = false, showCurrency = true) => {
      if (value === null || value === undefined || value === '-') return '-';
      
      if (selectedMetric.value === 'sales_amount' && showCurrency) {
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
    
    const formatPercentage = (value) => {
      if (value === null || value === undefined) return '-';
      const sign = value > 0 ? '+' : '';
      return sign + (value * 100).toFixed(2) + '%';
    };
    
    const getGrowthClass = (growth) => {
      if (growth > 0) return 'positive-growth';
      if (growth < 0) return 'negative-growth';
      return '';
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
      historicalData,
      forecastData,
      activeTab,
      selectedModel,
      selectedMetric,
      forecastPeriod,
      showConfidenceInterval,
      modelOptions,
      metricOptions,
      periodOptions,
      hasData,
      metricLabel,
      selectedModelLabel,
      forecastPeriodLabel,
      forecastStats,
      forecastDetails,
      fetchData,
      handleModelChange,
      handleMetricChange,
      handlePeriodChange,
      toggleConfidenceInterval,
      formatValue,
      formatPercentage,
      getGrowthClass
    };
  }
};
</script>

<style scoped>
.forecast-chart {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  align-items: center;
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

.forecast-summary {
  margin-top: 20px;
}

.positive-growth {
  color: #67C23A;
}

.negative-growth {
  color: #F56C6C;
}
</style>