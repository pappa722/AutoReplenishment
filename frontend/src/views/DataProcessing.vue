&lt;template>
  &lt;div class="data-processing">
    &lt;el-card class="upload-section">
      &lt;div slot="header">
        &lt;span>数据导入与处理&lt;/span>
      &lt;/div>
      &lt;el-upload
        class="upload-excel"
        drag
        :action="uploadUrl"
        :headers="headers"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        accept=".xlsx,.xls"
      >
        &lt;i class="el-icon-upload">&lt;/i>
        &lt;div class="el-upload__text">将Excel文件拖到此处，或&lt;em>点击上传&lt;/em>&lt;/div>
        &lt;div class="el-upload__tip" slot="tip">只能上传xlsx/xls文件&lt;/div>
      &lt;/el-upload>
    &lt;/el-card>

    &lt;el-card class="data-preview" v-if="previewData.length">
      &lt;div slot="header">
        &lt;span>数据预览&lt;/span>
        &lt;el-button style="float: right; margin-left: 10px" type="primary" size="small" @click="processData">
          开始处理
        &lt;/el-button>
      &lt;/div>
      &lt;el-table :data="previewData" border style="width: 100%">
        &lt;el-table-column
          v-for="(header, index) in tableHeaders"
          :key="index"
          :prop="header"
          :label="header"
        >
        &lt;/el-table-column>
      &lt;/el-table>
    &lt;/el-card>

    &lt;el-card class="processing-options" v-if="previewData.length">
      &lt;div slot="header">
        &lt;span>数据处理选项&lt;/span>
      &lt;/div>
      &lt;el-form :model="processingOptions" label-width="120px">
        &lt;el-form-item label="异常值检测方法">
          &lt;el-select v-model="processingOptions.outlierMethod">
            &lt;el-option label="Z-score" value="zscore">&lt;/el-option>
            &lt;el-option label="IQR" value="iqr">&lt;/el-option>
          &lt;/el-select>
        &lt;/el-form-item>
        &lt;el-form-item label="缺失值处理">
          &lt;el-select v-model="processingOptions.missingMethod">
            &lt;el-option label="均值填充" value="mean">&lt;/el-option>
            &lt;el-option label="中位数填充" value="median">&lt;/el-option>
            &lt;el-option label="前值填充" value="ffill">&lt;/el-option>
          &lt;/el-select>
        &lt;/el-form-item>
      &lt;/el-form>
    &lt;/el-card>

    &lt;el-card class="analysis-results" v-if="analysisResults">
      &lt;div slot="header">
        &lt;span>分析结果&lt;/span>
      &lt;/div>
      &lt;el-tabs v-model="activeTab">
        &lt;el-tab-pane label="异常值检测" name="outliers">
          &lt;div class="chart-container">
            &lt;div ref="outlierChart" style="width: 100%; height: 400px">&lt;/div>
          &lt;/div>
        &lt;/el-tab-pane>
        &lt;el-tab-pane label="销售模式分析" name="patterns">
          &lt;div class="chart-container">
            &lt;div ref="patternChart" style="width: 100%; height: 400px">&lt;/div>
          &lt;/div>
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
  name: 'DataProcessing',
  setup() {
    const store = useStore();
    const uploadUrl = `${import.meta.env.VITE_API_URL}/api/data-import/upload`;
    const headers = {
      Authorization: `Bearer ${store.state.auth.token}`
    };

    const previewData = ref([]);
    const tableHeaders = ref([]);
    const analysisResults = ref(null);
    const activeTab = ref('outliers');

    const processingOptions = reactive({
      outlierMethod: 'zscore',
      missingMethod: 'mean'
    });

    let outlierChart = null;
    let patternChart = null;

    onMounted(() => {
      if (analysisResults.value) {
        initCharts();
      }
    });

    const initCharts = () => {
      outlierChart = echarts.init(document.querySelector('.outlierChart'));
      patternChart = echarts.init(document.querySelector('.patternChart'));
      updateCharts();
    };

    const updateCharts = () => {
      if (!analysisResults.value) return;

      // 异常值检测图表配置
      const outlierOption = {
        title: { text: '异常值检测结果' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: analysisResults.value.dates },
        yAxis: { type: 'value' },
        series: [{
          name: '销售数据',
          type: 'line',
          data: analysisResults.value.values,
          markPoint: {
            data: analysisResults.value.outliers.map(point => ({
              name: '异常值',
              coord: [point.date, point.value],
              symbol: 'circle',
              symbolSize: 10
            }))
          }
        }]
      };

      // 销售模式分析图表配置
      const patternOption = {
        title: { text: '销售模式分析' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['原始数据', '趋势', '季节性', '残差'] },
        xAxis: { type: 'category', data: analysisResults.value.dates },
        yAxis: { type: 'value' },
        series: [
          {
            name: '原始数据',
            type: 'line',
            data: analysisResults.value.original
          },
          {
            name: '趋势',
            type: 'line',
            data: analysisResults.value.trend
          },
          {
            name: '季节性',
            type: 'line',
            data: analysisResults.value.seasonal
          },
          {
            name: '残差',
            type: 'line',
            data: analysisResults.value.residual
          }
        ]
      };

      outlierChart.setOption(outlierOption);
      patternChart.setOption(patternOption);
    };

    const handleUploadSuccess = (response) => {
      previewData.value = response.data.preview;
      tableHeaders.value = Object.keys(previewData.value[0] || {});
    };

    const handleUploadError = (error) => {
      console.error('上传失败:', error);
    };

    const beforeUpload = (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                      file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        this.$message.error('只能上传Excel文件！');
        return false;
      }
      return true;
    };

    const processData = async () => {
      try {
        const response = await store.dispatch('dataProcessing/processData', {
          options: processingOptions
        });
        analysisResults.value = response.data;
        initCharts();
      } catch (error) {
        console.error('数据处理失败:', error);
      }
    };

    return {
      uploadUrl,
      headers,
      previewData,
      tableHeaders,
      processingOptions,
      analysisResults,
      activeTab,
      handleUploadSuccess,
      handleUploadError,
      beforeUpload,
      processData
    };
  }
};
&lt;/script>

&lt;style scoped>
.data-processing {
  padding: 20px;
}

.upload-section,
.data-preview,
.processing-options,
.analysis-results {
  margin-bottom: 20px;
}

.chart-container {
  margin-top: 20px;
}

.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
}
&lt;/style>