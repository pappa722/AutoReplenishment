&lt;template>
  &lt;div class="anomaly-detection-chart">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="chart-header">
          &lt;span>{{ title }}&lt;/span>
          &lt;div class="chart-controls">
            &lt;el-select
              v-model="selectedMethod"
              placeholder="检测方法"
              size="small"
              @change="handleMethodChange"
            >
              &lt;el-option
                v-for="item in detectionMethods"
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
            &lt;el-tooltip content="调整检测灵敏度" placement="top">
              &lt;el-slider
                v-model="sensitivity"
                :min="1"
                :max="5"
                :step="1"
                :marks="sensitivityMarks"
                @change="handleSensitivityChange"
                style="width: 120px; margin-left: 16px;"
              />
            &lt;/el-tooltip>
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

      &lt;div class="anomaly-summary" v-if="hasData && !loading">
        &lt;el-descriptions :column="3" border>
          &lt;el-descriptions-item label="检测到的异常">
            {{ anomalyStats.totalAnomalies }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="异常占比">
            {{ formatPercentage(anomalyStats.anomalyRate) }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="最近异常">
            {{ anomalyStats.lastAnomalyDate || '-' }}
          &lt;/el-descriptions-item>
        &lt;/el-descriptions>

        &lt;div class="anomaly-list" v-if="anomalyStats.totalAnomalies > 0">
          &lt;h4>异常详情&lt;/h4>
          &lt;el-table
            :data="anomalyDetails"
            style="width: 100%"
            size="small"
            :max-height="200"
          >
            &lt;el-table-column prop="date" label="日期" width="120" />
            &lt;el-table-column prop="value" label="异常值">
              &lt;template #default="scope">
                {{ formatValue(scope.row.value) }}
              &lt;/template>
            &lt;/el-table-column>
            &lt;el-table-column prop="expected" label="预期范围">
              &lt;template #default="scope">
                {{ formatValue(scope.row.expected.min) }} ~ {{ formatValue(scope.row.expected.max) }}
              &lt;/template>
            &lt;/el-table-column>
            &lt;el-table-column prop="deviation" label="偏差">
              &lt;template #default="scope">
                &lt;span :class="getDeviationClass(scope.row.deviation)">
                  {{ formatPercentage(scope.row.deviation) }}
                &lt;/span>
              &lt;/template>
            &lt;/el-table-column>
          &lt;/el-table>
        &lt;/div>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts/core';
import { LineChart, ScatterChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  LineChart,
  ScatterChart,
  CanvasRenderer
]);

export default {
  name: 'AnomalyDetectionChart',
  props: {
    title: {
      type: String,
      default: '异常检测'
    },
    apiUrl: {
      type: String,
      required: true
    },
    defaultMethod: {
      type: String,
      default: 'zscore'
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
    const anomalyData = ref([]);
    
    // 选项
    const selectedMethod = ref(props.defaultMethod);
    const selectedMetric = ref(props.defaultMetric);
    const sensitivity = ref(3);
    
    // 检测方法选项
    const detectionMethods = [
      { label: 'Z-Score', value: 'zscore' },
      { label: 'IQR', value: 'iqr' },
      { label: '移动平均', value: 'moving_average' },
      { label: '指数平滑', value: 'exponential_smoothing' }
    ];
    
    // 指标选项
    const metricOptions = [
      { label: '销售额', value: 'sales_amount' },
      { label: '销售数量', value: 'sales_quantity' },
      { label: '订单数', value: 'order_count' },
      { label: '平均客单价', value: 'average_order_value' }
    ];
    
    // 灵敏度标记
    const sensitivityMarks = {
      1: '低',
      3: '中',
      5: '高'
    };
    
    // 计算属性
    const hasData = computed(() => chartData.value && chartData.value.length > 0);
    
    const metricLabel = computed(() => {
      const option = metricOptions.find(opt => opt.value === selectedMetric.value);
      return option ? option.label : '';
    });
    
    const anomalyStats = computed(() => {
      if (!anomalyData.value || !chartData.value) return {
        totalAnomalies: 0,
        anomalyRate: 0,
        lastAnomalyDate: null
      };
      
      const totalAnomalies = anomalyData.value.length;
      const anomalyRate = totalAnomalies / chartData.value.length;
      const lastAnomaly = anomalyData.value[anomalyData.value.length - 1];
      
      return {
        totalAnomalies,
        anomalyRate,
        lastAnomalyDate: lastAnomaly ? lastAnomaly.date : null
      };
    });
    
    const anomalyDetails = computed(() => {
      return anomalyData.value.map(anomaly => ({
        date: anomaly.date,
        value: anomaly.value,
        expected: anomaly.expected,
        deviation: (anomaly.value - anomaly.expected.avg) / anomaly.expected.avg
      }));
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
            type: 'cross'
          },
          formatter: function(params) {
            let result = params[0].axisValue + '&lt;br/>';
            
            // 添加实际值
            result += `${metricLabel.value}: ${formatValue(params[0].value)}&lt;br/>`;
            
            // 如果是异常点，添加预期范围
            const anomaly = anomalyData.value.find(a => a.date === params[0].axisValue);
            if (anomaly) {
              result += `预期范围: ${formatValue(anomaly.expected.min)} ~ ${formatValue(anomaly.expected.max)}&lt;br/>`;
              const deviation = (anomaly.value - anomaly.expected.avg) / anomaly.expected.avg;
              result += `偏差: ${formatPercentage(deviation)}`;
            }
            
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
            name: '实际值',
            type: 'line',
            data: [],
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2
            },
            areaStyle: {
              opacity: 0.1
            }
          },
          {
            name: '异常点',
            type: 'scatter',
            data: [],
            symbolSize: 10,
            itemStyle: {
              color: '#F56C6C'
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
        ]
      });
      
      window.addEventListener('resize', handleResize);
    };
    
    const updateChart = () => {
      if (!chartInstance || !hasData.value) return;
      
      const xAxisData = chartData.value.map(item => item.date);
      const normalData = chartData.value.map(item => item.value);
      const anomalyPoints = anomalyData.value.map(item => [
        item.date,
        item.value
      ]);
      
      chartInstance.setOption({
        xAxis: {
          data: xAxisData
        },
        series: [
          {
            name: '实际值',
            data: normalData
          },
          {
            name: '异常点',
            data: anomalyPoints
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
          method: selectedMethod.value,
          metric: selectedMetric.value,
          sensitivity: sensitivity.value
        };
        
        // 模拟API请求
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟数据
        const today = new Date();
        const data = [];
        const anomalies = [];
        
        for (let i = 29; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          const formattedDate = date.toISOString().split('T')[0];
          
          // 生成基础值
          let baseValue;
          if (selectedMetric.value === 'sales_amount') {
            baseValue = Math.floor(Math.random() * 10000) + 5000;
          } else if (selectedMetric.value === 'sales_quantity') {
            baseValue = Math.floor(Math.random() * 100) + 50;
          } else if (selectedMetric.value === 'order_count') {
            baseValue = Math.floor(Math.random() * 50) + 10;
          } else {
            baseValue = Math.floor(Math.random() * 200) + 100;
          }
          
          // 添加趋势
          baseValue = baseValue * (1 + i * 0.01);
          
          // 添加周末效应
          const dayOfWeek = date.getDay();
          if (dayOfWeek === 0 || dayOfWeek === 6) {
            baseValue = baseValue * 1.2;
          }
          
          // 随机添加异常值
          if (Math.random() < 0.1) { // 10%的概率出现异常
            const anomalyFactor = Math.random() < 0.5 ? 0.5 : 2; // 50%概率偏高或偏低
            const anomalyValue = baseValue * anomalyFactor;
            
            data.push({
              date: formattedDate,
              value: anomalyValue
            });
            
            anomalies.push({
              date: formattedDate,
              value: anomalyValue,
              expected: {
                min: baseValue * 0.8,
                max: baseValue * 1.2,
                avg: baseValue
              }
            });
          } else {
            data.push({
              date: formattedDate,
              value: baseValue
            });
          }
        }
        
        chartData.value = data;
        anomalyData.value = anomalies;
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
    
    const handleMethodChange = () => {
      fetchData();
    };
    
    const handleMetricChange = () => {
      fetchData();
    };
    
    const handleSensitivityChange = () => {
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
    
    const formatPercentage = (value) => {
      if (value === null || value === undefined) return '-';
      const sign = value > 0 ? '+' : '';
      return sign + (value * 100).toFixed(2) + '%';
    };
    
    const getDeviationClass = (deviation) => {
      if (deviation > 0.5) return 'high-deviation';
      if (deviation > 0.2) return 'medium-deviation';
      if (deviation < -0.5) return 'high-deviation';
      if (deviation < -0.2) return 'medium-deviation';
      return 'normal-deviation';
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
      anomalyData,
      selectedMethod,
      selectedMetric,
      sensitivity,
      detectionMethods,
      metricOptions,
      sensitivityMarks,
      hasData,
      metricLabel,
      anomalyStats,
      anomalyDetails,
      fetchData,
      handleMethodChange,
      handleMetricChange,
      handleSensitivityChange,
      formatValue,
      formatPercentage,
      getDeviationClass
    };
  }
};
&lt;/script>

&lt;style scoped>
.anomaly-detection-chart {
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

.anomaly-summary {
  margin-top: 20px;
}

.anomaly-list {
  margin-top: 20px;
}

.anomaly-list h4 {
  margin-bottom: 10px;
  color: #303133;
}

.high-deviation {
  color: #F56C6C;
  font-weight: bold;
}

.medium-deviation {
  color: #E6A23C;
}

.normal-deviation {
  color: #67C23A;
}
&lt;/style>