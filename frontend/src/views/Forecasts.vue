&lt;template>
  &lt;div class="forecasts">
    &lt;el-card class="forecast-settings">
      &lt;div slot="header">
        &lt;span>预测设置&lt;/span>
      &lt;/div>
      &lt;el-form :model="forecastSettings" label-width="120px">
        &lt;el-form-item label="预测模型">
          &lt;el-select v-model="forecastSettings.model" @change="handleModelChange">
            &lt;el-option label="SARIMA" value="sarima">&lt;/el-option>
            &lt;el-option label="随机森林" value="randomforest">&lt;/el-option>
          &lt;/el-select>
        &lt;/el-form-item>

        &lt;el-form-item label="预测周期">
          &lt;el-input-number
            v-model="forecastSettings.periods"
            :min="1"
            :max="90"
            :step="1"
          >&lt;/el-input-number>
          &lt;span class="unit">天&lt;/span>
        &lt;/el-form-item>

        &lt;el-form-item label="置信区间">
          &lt;el-select v-model="forecastSettings.confidenceLevel">
            &lt;el-option label="90%" value="0.9">&lt;/el-option>
            &lt;el-option label="95%" value="0.95">&lt;/el-option>
            &lt;el-option label="99%" value="0.99">&lt;/el-option>
          &lt;/el-select>
        &lt;/el-form-item>

        &lt;template v-if="forecastSettings.model === 'sarima'">
          &lt;el-form-item label="SARIMA参数">
            &lt;el-row :gutter="20">
              &lt;el-col :span="8">
                &lt;el-form-item label="p">
                  &lt;el-input-number v-model="forecastSettings.sarima.p" :min="0" :max="5">&lt;/el-input-number>
                &lt;/el-form-item>
              &lt;/el-col>
              &lt;el-col :span="8">
                &lt;el-form-item label="d">
                  &lt;el-input-number v-model="forecastSettings.sarima.d" :min="0" :max="2">&lt;/el-input-number>
                &lt;/el-form-item>
              &lt;/el-col>
              &lt;el-col :span="8">
                &lt;el-form-item label="q">
                  &lt;el-input-number v-model="forecastSettings.sarima.q" :min="0" :max="5">&lt;/el-input-number>
                &lt;/el-form-item>
              &lt;/el-col>
            &lt;/el-row>
          &lt;/el-form-item>
        &lt;/template>

        &lt;template v-if="forecastSettings.model === 'randomforest'">
          &lt;el-form-item label="树的数量">
            &lt;el-input-number
              v-model="forecastSettings.randomForest.n_estimators"
              :min="10"
              :max="1000"
              :step="10"
            >&lt;/el-input-number>
          &lt;/el-form-item>
        &lt;/template>

        &lt;el-form-item>
          &lt;el-button type="primary" @click="generateForecast">生成预测&lt;/el-button>
        &lt;/el-form-item>
      &lt;/el-form>
    &lt;/el-card>

    &lt;el-card class="forecast-results" v-if="forecastResults">
      &lt;div slot="header">
        &lt;span>预测结果&lt;/span>
        &lt;el-button
          style="float: right; margin-left: 10px"
          type="text"
          @click="exportForecast"
        >
          导出预测结果
        &lt;/el-button>
      &lt;/div>

      &lt;el-tabs v-model="activeTab">
        &lt;el-tab-pane label="预测图表" name="chart">
          &lt;div class="chart-container">
            &lt;div ref="forecastChart" style="width: 100%; height: 500px">&lt;/div>
          &lt;/div>
        &lt;/el-tab-pane>

        &lt;el-tab-pane label="预测数据" name="data">
          &lt;el-table :data="forecastResults.data" border style="width: 100%">
            &lt;el-table-column prop="date" label="日期" width="180">&lt;/el-table-column>
            &lt;el-table-column prop="forecast" label="预测值">&lt;/el-table-column>
            &lt;el-table-column prop="lower_bound" label="下限">&lt;/el-table-column>
            &lt;el-table-column prop="upper_bound" label="上限">&lt;/el-table-column>
          &lt;/el-table>
        &lt;/el-tab-pane>

        &lt;el-tab-pane label="模型评估" name="evaluation">
          &lt;el-descriptions border>
            &lt;el-descriptions-item label="平均绝对误差 (MAE)">
              {{ forecastResults.evaluation.mae }}
            &lt;/el-descriptions-item>
            &lt;el-descriptions-item label="均方根误差 (RMSE)">
              {{ forecastResults.evaluation.rmse }}
            &lt;/el-descriptions-item>
            &lt;el-descriptions-item label="平均绝对百分比误差 (MAPE)">
              {{ forecastResults.evaluation.mape }}%
            &lt;/el-descriptions-item>
          &lt;/el-descriptions>
        &lt;/el-tab-pane>
      &lt;/el-tabs>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script>
import * as echarts from 'echarts';
import { ref, reactive, onMounted } from 'vue';
import { useStore } from 'vuex';

export default {
  name: 'Forecasts',
  setup() {
    const store = useStore();
    const forecastResults = ref(null);
    const activeTab = ref('chart');
    let forecastChart = null;

    const forecastSettings = reactive({
      model: 'sarima',
      periods: 30,
      confidenceLevel: '0.95',
      sarima: {
        p: 1,
        d: 1,
        q: 1
      },
      randomForest: {
        n_estimators: 100
      }
    });

    onMounted(() => {
      if (forecastResults.value) {
        initChart();
      }
    });

    const initChart = () => {
      forecastChart = echarts.init(document.querySelector('.forecastChart'));
      updateChart();
    };

    const updateChart = () => {
      if (!forecastResults.value) return;

      const option = {
        title: {
          text: '销量预测结果'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['历史数据', '预测值', '置信区间']
        },
        xAxis: {
          type: 'category',
          data: [
            ...forecastResults.value.historical_dates,
            ...forecastResults.value.forecast_dates
          ]
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '历史数据',
            type: 'line',
            data: forecastResults.value.historical_data,
            color: '#409EFF'
          },
          {
            name: '预测值',
            type: 'line',
            data: Array(forecastResults.value.historical_data.length)
              .fill('-')
              .concat(forecastResults.value.forecasts),
            color: '#67C23A'
          },
          {
            name: '置信区间',
            type: 'line',
            data: Array(forecastResults.value.historical_data.length)
              .fill('-')
              .concat(forecastResults.value.upper_bound),
            lineStyle: {
              opacity: 0.3
            },
            areaStyle: {
              opacity: 0.3
            }
          },
          {
            name: '置信区间',
            type: 'line',
            data: Array(forecastResults.value.historical_data.length)
              .fill('-')
              .concat(forecastResults.value.lower_bound),
            lineStyle: {
              opacity: 0.3
            },
            areaStyle: {
              opacity: 0.3
            }
          }
        ]
      };

      forecastChart.setOption(option);
    };

    const handleModelChange = (value) => {
      // 重置相关参数
      if (value === 'sarima') {
        forecastSettings.sarima = {
          p: 1,
          d: 1,
          q: 1
        };
      } else {
        forecastSettings.randomForest = {
          n_estimators: 100
        };
      }
    };

    const generateForecast = async () => {
      try {
        const response = await store.dispatch('forecasts/generateForecast', forecastSettings);
        forecastResults.value = response.data;
        initChart();
      } catch (error) {
        console.error('预测生成失败:', error);
      }
    };

    const exportForecast = () => {
      if (!forecastResults.value) return;

      const data = forecastResults.value.data;
      const csvContent = 'data:text/csv;charset=utf-8,' +
        '日期,预测值,下限,上限\n' +
        data.map(row => `${row.date},${row.forecast},${row.lower_bound},${row.upper_bound}`).join('\n');

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', '预测结果.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    return {
      forecastSettings,
      forecastResults,
      activeTab,
      handleModelChange,
      generateForecast,
      exportForecast
    };
  }
};
&lt;/script>

&lt;style scoped>
.forecasts {
  padding: 20px;
}

.forecast-settings,
.forecast-results {
  margin-bottom: 20px;
}

.chart-container {
  margin-top: 20px;
}

.unit {
  margin-left: 10px;
}

.el-descriptions {
  margin: 20px 0;
}
&lt;/style>