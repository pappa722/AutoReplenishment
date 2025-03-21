&lt;template>
  &lt;div class="forecast-config-container">
    &lt;!-- 模型选择卡片 -->
    &lt;el-card class="model-card">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>预测模型选择&lt;/span>
          &lt;div class="header-actions">
            &lt;el-button type="success" @click="saveModelConfig">保存配置&lt;/el-button>
            &lt;el-button type="primary" @click="applyConfig">应用配置&lt;/el-button>
          &lt;/div>
        &lt;/div>
      &lt;/template>

      &lt;el-form :model="modelConfig" label-width="120px">
        &lt;el-form-item label="预测模型">
          &lt;el-radio-group v-model="modelConfig.modelType" @change="handleModelChange">
            &lt;el-radio label="sarima">SARIMA模型&lt;/el-radio>
            &lt;el-radio label="randomforest">随机森林&lt;/el-radio>
            &lt;el-radio label="prophet">Prophet模型&lt;/el-radio>
            &lt;el-radio label="ensemble">集成模型&lt;/el-radio>
          &lt;/el-radio-group>
        &lt;/el-form-item>
        
        &lt;el-divider content-position="left">模型参数配置&lt;/el-divider>
        
        &lt;!-- SARIMA模型参数 -->
        &lt;template v-if="modelConfig.modelType === 'sarima'">
          &lt;el-form-item label="AR阶数(p)">
            &lt;el-input-number v-model="modelConfig.sarima.p" :min="0" :max="5" />
          &lt;/el-form-item>
          &lt;el-form-item label="差分阶数(d)">
            &lt;el-input-number v-model="modelConfig.sarima.d" :min="0" :max="2" />
          &lt;/el-form-item>
          &lt;el-form-item label="MA阶数(q)">
            &lt;el-input-number v-model="modelConfig.sarima.q" :min="0" :max="5" />
          &lt;/el-form-item>
          &lt;el-form-item label="季节性AR阶数(P)">
            &lt;el-input-number v-model="modelConfig.sarima.P" :min="0" :max="2" />
          &lt;/el-form-item>
          &lt;el-form-item label="季节性差分(D)">
            &lt;el-input-number v-model="modelConfig.sarima.D" :min="0" :max="1" />
          &lt;/el-form-item>
          &lt;el-form-item label="季节性MA阶数(Q)">
            &lt;el-input-number v-model="modelConfig.sarima.Q" :min="0" :max="2" />
          &lt;/el-form-item>
          &lt;el-form-item label="季节周期(s)">
            &lt;el-select v-model="modelConfig.sarima.s">
              &lt;el-option label="每周(7)" :value="7" />
              &lt;el-option label="每月(30)" :value="30" />
              &lt;el-option label="每季度(90)" :value="90" />
              &lt;el-option label="每年(365)" :value="365" />
            &lt;/el-select>
          &lt;/el-form-item>
          &lt;el-form-item label="自动参数优化">
            &lt;el-switch v-model="modelConfig.sarima.autoParams" />
          &lt;/el-form-item>
        &lt;/template>
        
        &lt;!-- 随机森林模型参数 -->
        &lt;template v-if="modelConfig.modelType === 'randomforest'">
          &lt;el-form-item label="树的数量">
            &lt;el-input-number v-model="modelConfig.randomforest.n_estimators" :min="10" :max="500" :step="10" />
          &lt;/el-form-item>
          &lt;el-form-item label="最大深度">
            &lt;el-input-number v-model="modelConfig.randomforest.max_depth" :min="3" :max="30" />
          &lt;/el-form-item>
          &lt;el-form-item label="最小叶节点样本数">
            &lt;el-input-number v-model="modelConfig.randomforest.min_samples_leaf" :min="1" :max="20" />
          &lt;/el-form-item>
          &lt;el-form-item label="特征选择">
            &lt;el-checkbox-group v-model="modelConfig.randomforest.features">
              &lt;el-checkbox label="day_of_week">星期几&lt;/el-checkbox>
              &lt;el-checkbox label="month">月份&lt;/el-checkbox>
              &lt;el-checkbox label="is_holiday">是否节假日&lt;/el-checkbox>
              &lt;el-checkbox label="is_weekend">是否周末&lt;/el-checkbox>
              &lt;el-checkbox label="previous_sales">历史销量&lt;/el-checkbox>
              &lt;el-checkbox label="price">价格&lt;/el-checkbox>
              &lt;el-checkbox label="promotion">促销&lt;/el-checkbox>
              &lt;el-checkbox label="weather">天气&lt;/el-checkbox>
            &lt;/el-checkbox-group>
          &lt;/el-form-item>
        &lt;/template>
        
        &lt;!-- Prophet模型参数 -->
        &lt;template v-if="modelConfig.modelType === 'prophet'">
          &lt;el-form-item label="增长模式">
            &lt;el-select v-model="modelConfig.prophet.growth">
              &lt;el-option label="线性增长" value="linear" />
              &lt;el-option label="逻辑增长" value="logistic" />
            &lt;/el-select>
          &lt;/el-form-item>
          &lt;el-form-item label="季节性模式">
            &lt;el-select v-model="modelConfig.prophet.seasonality_mode">
              &lt;el-option label="加法模式" value="additive" />
              &lt;el-option label="乘法模式" value="multiplicative" />
            &lt;/el-select>
          &lt;/el-form-item>
          &lt;el-form-item label="季节性先验尺度">
            &lt;el-slider v-model="modelConfig.prophet.seasonality_prior_scale" :min="0.01" :max="10" :step="0.01" show-input />
          &lt;/el-form-item>
          &lt;el-form-item label="节假日先验尺度">
            &lt;el-slider v-model="modelConfig.prophet.holidays_prior_scale" :min="0.01" :max="10" :step="0.01" show-input />
          &lt;/el-form-item>
          &lt;el-form-item label="变点先验尺度">
            &lt;el-slider v-model="modelConfig.prophet.changepoint_prior_scale" :min="0.001" :max="0.5" :step="0.001" show-input />
          &lt;/el-form-item>
          &lt;el-form-item label="包含中国节假日">
            &lt;el-switch v-model="modelConfig.prophet.include_holidays" />
          &lt;/el-form-item>
        &lt;/template>
        
        &lt;!-- 集成模型参数 -->
        &lt;template v-if="modelConfig.modelType === 'ensemble'">
          &lt;el-form-item label="集成模型">
            &lt;el-checkbox-group v-model="modelConfig.ensemble.models">
              &lt;el-checkbox label="sarima">SARIMA&lt;/el-checkbox>
              &lt;el-checkbox label="randomforest">随机森林&lt;/el-checkbox>
              &lt;el-checkbox label="prophet">Prophet&lt;/el-checkbox>
              &lt;el-checkbox label="arima">ARIMA&lt;/el-checkbox>
              &lt;el-checkbox label="exponential">指数平滑&lt;/el-checkbox>
            &lt;/el-checkbox-group>
          &lt;/el-form-item>
          &lt;el-form-item label="集成方法">
            &lt;el-select v-model="modelConfig.ensemble.method">
              &lt;el-option label="简单平均" value="average" />
              &lt;el-option label="加权平均" value="weighted" />
              &lt;el-option label="投票法" value="voting" />
              &lt;el-option label="堆叠法" value="stacking" />
            &lt;/el-select>
          &lt;/el-form-item>
          &lt;el-form-item v-if="modelConfig.ensemble.method === 'weighted'" label="权重配置">
            &lt;div v-for="model in modelConfig.ensemble.models" :key="model" class="weight-item">
              &lt;span>{{ getModelName(model) }}:&lt;/span>
              &lt;el-slider
                v-model="modelConfig.ensemble.weights[model]"
                :min="0"
                :max="1"
                :step="0.01"
                :format-tooltip="percentFormat"
              />
            &lt;/div>
          &lt;/el-form-item>
        &lt;/template>
      &lt;/el-form>
    &lt;/el-card>

    &lt;!-- 预测设置卡片 -->
    &lt;el-card class="forecast-settings-card">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>预测设置&lt;/span>
        &lt;/div>
      &lt;/template>

      &lt;el-form :model="forecastSettings" label-width="120px">
        &lt;el-form-item label="预测周期">
          &lt;el-select v-model="forecastSettings.forecastPeriod">
            &lt;el-option label="未来7天" :value="7" />
            &lt;el-option label="未来14天" :value="14" />
            &lt;el-option label="未来30天" :value="30" />
            &lt;el-option label="未来90天" :value="90" />
          &lt;/el-select>
        &lt;/el-form-item>
        
        &lt;el-form-item label="历史数据范围">
          &lt;el-select v-model="forecastSettings.historyRange">
            &lt;el-option label="过去30天" :value="30" />
            &lt;el-option label="过去90天" :value="90" />
            &lt;el-option label="过去180天" :value="180" />
            &lt;el-option label="过去365天" :value="365" />
            &lt;el-option label="全部历史" :value="-1" />
          &lt;/el-select>
        &lt;/el-form-item>
        
        &lt;el-form-item label="预测粒度">
          &lt;el-select v-model="forecastSettings.granularity">
            &lt;el-option label="日级别" value="daily" />
            &lt;el-option label="周级别" value="weekly" />
            &lt;el-option label="月级别" value="monthly" />
          &lt;/el-select>
        &lt;/el-form-item>
        
        &lt;el-form-item label="置信区间">
          &lt;el-select v-model="forecastSettings.confidenceInterval">
            &lt;el-option label="80%" :value="80" />
            &lt;el-option label="90%" :value="90" />
            &lt;el-option label="95%" :value="95" />
            &lt;el-option label="99%" :value="99" />
          &lt;/el-select>
        &lt;/el-form-item>
        
        &lt;el-form-item label="自动更新频率">
          &lt;el-select v-model="forecastSettings.updateFrequency">
            &lt;el-option label="每日" value="daily" />
            &lt;el-option label="每周" value="weekly" />
            &lt;el-option label="每月" value="monthly" />
            &lt;el-option label="手动" value="manual" />
          &lt;/el-select>
        &lt;/el-form-item>
      &lt;/el-form>
    &lt;/el-card>

    &lt;!-- 高级配置卡片 -->
    &lt;el-card class="advanced-settings-card">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>高级配置&lt;/span>
          &lt;el-switch v-model="showAdvancedSettings" active-text="显示高级选项" />
        &lt;/div>
      &lt;/template>

      &lt;div v-if="showAdvancedSettings">
        &lt;el-form :model="advancedSettings" label-width="180px">
          &lt;el-form-item label="异常值检测方法">
            &lt;el-select v-model="advancedSettings.outlierDetection">
              &lt;el-option label="IQR方法" value="iqr" />
              &lt;el-option label="Z-Score方法" value="zscore" />
              &lt;el-option label="隔离森林" value="isolation_forest" />
              &lt;el-option label="不处理" value="none" />
            &lt;/el-select>
          &lt;/el-form-item>
          
          &lt;el-form-item label="缺失值处理">
            &lt;el-select v-model="advancedSettings.missingValueStrategy">
              &lt;el-option label="线性插值" value="linear" />
              &lt;el-option label="前向填充" value="forward_fill" />
              &lt;el-option label="均值填充" value="mean" />
              &lt;el-option label="中位数填充" value="median" />
              &lt;el-option label="不处理" value="none" />
            &lt;/el-select>
          &lt;/el-form-item>
          
          &lt;el-form-item label="交叉验证折数">
            &lt;el-input-number v-model="advancedSettings.cvFolds" :min="2" :max="10" />
          &lt;/el-form-item>
          
          &lt;el-form-item label="特征工程">
            &lt;el-checkbox-group v-model="advancedSettings.featureEngineering">
              &lt;el-checkbox label="lag_features">滞后特征&lt;/el-checkbox>
              &lt;el-checkbox label="rolling_features">滚动统计特征&lt;/el-checkbox>
              &lt;el-checkbox label="holiday_features">节假日特征&lt;/el-checkbox>
              &lt;el-checkbox label="promotion_features">促销特征&lt;/el-checkbox>
              &lt;el-checkbox label="weather_features">天气特征&lt;/el-checkbox>
            &lt;/el-checkbox-group>
          &lt;/el-form-item>
          
          &lt;el-form-item label="数据标准化">
            &lt;el-select v-model="advancedSettings.normalization">
              &lt;el-option label="MinMax标准化" value="minmax" />
              &lt;el-option label="Z-Score标准化" value="zscore" />
              &lt;el-option label="不标准化" value="none" />
            &lt;/el-select>
          &lt;/el-form-item>
        &lt;/el-form>
      &lt;/div>
    &lt;/el-card>

    &lt;!-- 模型评估卡片 -->
    &lt;el-card class="model-evaluation-card" v-if="modelEvaluation.available">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>模型评估&lt;/span>
          &lt;el-button type="primary" @click="evaluateModel">评估模型&lt;/el-button>
        &lt;/div>
      &lt;/template>

      &lt;el-row :gutter="20">
        &lt;el-col :span="12">
          &lt;h4>评估指标&lt;/h4>
          &lt;el-table :data="modelEvaluation.metrics" style="width: 100%">
            &lt;el-table-column prop="name" label="指标" />
            &lt;el-table-column prop="value" label="值" />
          &lt;/el-table>
        &lt;/el-col>
        &lt;el-col :span="12">
          &lt;h4>预测准确度&lt;/h4>
          &lt;div class="accuracy-chart" ref="accuracyChartRef">
            &lt;!-- 图表将在mounted中渲染 -->
          &lt;/div>
        &lt;/el-col>
      &lt;/el-row>

      &lt;el-divider />

      &lt;div class="model-comparison" v-if="modelEvaluation.comparison.length > 0">
        &lt;h4>模型比较&lt;/h4>
        &lt;el-table :data="modelEvaluation.comparison" style="width: 100%">
          &lt;el-table-column prop="model" label="模型" />
          &lt;el-table-column prop="rmse" label="RMSE" />
          &lt;el-table-column prop="mae" label="MAE" />
          &lt;el-table-column prop="mape" label="MAPE" />
          &lt;el-table-column prop="r2" label="R²" />
        &lt;/el-table>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'

// 模型配置
const modelConfig = reactive({
  modelType: 'sarima',
  sarima: {
    p: 1,
    d: 1,
    q: 1,
    P: 1,
    D: 0,
    Q: 1,
    s: 7,
    autoParams: true
  },
  randomforest: {
    n_estimators: 100,
    max_depth: 10,
    min_samples_leaf: 2,
    features: ['day_of_week', 'month', 'is_holiday', 'previous_sales', 'price', 'promotion']
  },
  prophet: {
    growth: 'linear',
    seasonality_mode: 'additive',
    seasonality_prior_scale: 10,
    holidays_prior_scale: 10,
    changepoint_prior_scale: 0.05,
    include_holidays: true
  },
  ensemble: {
    models: ['sarima', 'randomforest', 'prophet'],
    method: 'weighted',
    weights: {
      sarima: 0.4,
      randomforest: 0.3,
      prophet: 0.3,
      arima: 0,
      exponential: 0
    }
  }
})

// 高级配置开关
const showAdvancedSettings = ref(false)

// 高级配置
const advancedSettings = reactive({
  outlierDetection: 'zscore',
  missingValueStrategy: 'linear',
  cvFolds: 5,
  featureEngineering: ['lag_features', 'rolling_features', 'holiday_features'],
  normalization: 'minmax'
})

// 模型评估数据
const modelEvaluation = reactive({
  available: false,
  metrics: [],
  comparison: [],
  accuracyData: {
    dates: [],
    actual: [],
    predicted: []
  }
})

// 预测设置
const forecastSettings = reactive({
  forecastPeriod: 14,
  historyRange: 90,
  granularity: 'daily',
  confidenceInterval: 95,
  updateFrequency: 'weekly'
})

// 图表引用
const accuracyChartRef = ref(null)
let accuracyChart = null

// 初始化
onMounted(async () => {
  await loadModelConfig()
  await loadForecastSettings()
  await loadAdvancedSettings()
  await loadModelEvaluation()
})

// 加载高级设置
const loadAdvancedSettings = async () => {
  try {
    const response = await axios.get('/api/forecasts/advanced-settings')
    if (response.data) {
      Object.assign(advancedSettings, response.data)
    }
  } catch (error) {
    ElMessage.error('加载高级设置失败')
  }
}

// 加载模型评估数据
const loadModelEvaluation = async () => {
  try {
    const response = await axios.get('/api/forecasts/evaluation')
    if (response.data) {
      modelEvaluation.available = true
      modelEvaluation.metrics = response.data.metrics
      modelEvaluation.comparison = response.data.comparison
      modelEvaluation.accuracyData = response.data.accuracyData
      
      await nextTick()
      initAccuracyChart()
    }
  } catch (error) {
    modelEvaluation.available = false
    console.error('加载模型评估数据失败:', error)
  }
}

// 初始化准确度图表
const initAccuracyChart = () => {
  if (!accuracyChartRef.value) return
  
  accuracyChart = echarts.init(accuracyChartRef.value)
  
  const option = {
    title: {
      text: '预测准确度分析'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['实际值', '预测值']
    },
    xAxis: {
      type: 'category',
      data: modelEvaluation.accuracyData.dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '实际值',
        type: 'line',
        data: modelEvaluation.accuracyData.actual
      },
      {
        name: '预测值',
        type: 'line',
        data: modelEvaluation.accuracyData.predicted
      }
    ]
  }
  
  accuracyChart.setOption(option)
}

// 评估模型
const evaluateModel = async () => {
  try {
    await ElMessageBox.confirm(
      '模型评估将使用测试数据集进行验证，可能需要一些时间。是否继续？',
      '评估模型',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    const response = await axios.post('/api/forecasts/evaluate', {
      modelType: modelConfig.modelType,
      sarima: modelConfig.sarima,
      randomforest: modelConfig.randomforest,
      prophet: modelConfig.prophet,
      ensemble: modelConfig.ensemble,
      forecastSettings: forecastSettings,
      advancedSettings: advancedSettings
    })
    
    if (response.data) {
      await loadModelEvaluation()
      ElMessage.success('模型评估完成')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('模型评估失败')
    }
  }
}

// 格式化百分比
const percentFormat = (val) => {
  return `${(val * 100).toFixed(0)}%`
}

// 获取模型名称
const getModelName = (model) => {
  const modelNames = {
    sarima: 'SARIMA',
    randomforest: '随机森林',
    prophet: 'Prophet',
    arima: 'ARIMA',
    exponential: '指数平滑'
  }
  return modelNames[model] || model
}

// 加载预测设置
const loadForecastSettings = async () => {
  try {
    const response = await axios.get('/api/forecasts/settings')
    if (response.data) {
      Object.assign(forecastSettings, response.data)
    }
  } catch (error) {
    ElMessage.error('加载预测设置失败')
  }
}

// 加载模型配置
const loadModelConfig = async () => {
  try {
    const response = await axios.get('/api/forecasts/model-config')
    
    // 合并配置，保留默认值
    if (response.data.modelType) {
      modelConfig.modelType = response.data.modelType
    }
    
    if (response.data.sarima) {
      Object.assign(modelConfig.sarima, response.data.sarima)
    }
    
    if (response.data.randomforest) {
      Object.assign(modelConfig.randomforest, response.data.randomforest)
    }
    
    if (response.data.prophet) {
      Object.assign(modelConfig.prophet, response.data.prophet)
    }
    
    if (response.data.ensemble) {
      Object.assign(modelConfig.ensemble, response.data.ensemble)
    }
  } catch (error) {
    ElMessage.error('加载模型配置失败')
  }
}

// 处理模型类型变化
const handleModelChange = (value) => {
  // 可以在这里添加模型切换时的逻辑
}

// 保存模型配置
const saveModelConfig = async () => {
  try {
    await axios.post('/api/forecasts/model-config', {
      modelType: modelConfig.modelType,
      sarima: modelConfig.sarima,
      randomforest: modelConfig.randomforest,
      prophet: modelConfig.prophet,
      ensemble: modelConfig.ensemble
    })
    
    // 同时保存预测设置
    await axios.post('/api/forecasts/settings', forecastSettings)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('保存配置失败')
  }
}

// 应用配置
const applyConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '应用配置将使用当前设置重新训练模型，可能需要一些时间。是否继续？',
      '应用配置',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await axios.post('/api/forecasts/apply-config', {
      modelType: modelConfig.modelType,
      sarima: modelConfig.sarima,
      randomforest: modelConfig.randomforest,
      prophet: modelConfig.prophet,
      ensemble: modelConfig.ensemble,
      forecastSettings: forecastSettings
    })
    
    if (response.data.taskId) {
      ElMessage.success(`配置应用成功，任务ID: ${response.data.taskId}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('应用配置失败')
    }
  }
}
&lt;/script>

&lt;style scoped>
.forecast-config-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.model-card,
.forecast-settings-card,
.advanced-settings-card,
.model-evaluation-card {
  margin-bottom: 20px;
}

.weight-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px;
}

.weight-item span {
  min-width: 100px;
}

.weight-item .el-slider {
  flex: 1;
}

.accuracy-chart {
  height: 300px;
  width: 100%;
}
&lt;/style>