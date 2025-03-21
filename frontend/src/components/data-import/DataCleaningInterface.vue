&lt;template>
  &lt;div class="data-cleaning-container">
    &lt;el-card class="data-cleaning-card">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;h2>数据清洗与标准化&lt;/h2>
          &lt;el-button-group>
            &lt;el-button type="primary" @click="applyCleaningRules" :loading="processing">
              应用清洗规则
            &lt;/el-button>
            &lt;el-button @click="previewOriginalData">查看原始数据&lt;/el-button>
            &lt;el-button @click="saveCleanedData" :disabled="!hasCleanedData">保存清洗结果&lt;/el-button>
          &lt;/el-button-group>
        &lt;/div>
      &lt;/template>

      &lt;div class="cleaning-options">
        &lt;el-collapse v-model="activeCollapse">
          &lt;el-collapse-item title="数据源选择" name="dataSource">
            &lt;el-form :model="dataSourceForm" label-width="120px">
              &lt;el-form-item label="数据类型">
                &lt;el-select v-model="dataSourceForm.dataType" placeholder="选择数据类型">
                  &lt;el-option label="销售数据" value="sales" />
                  &lt;el-option label="库存数据" value="inventory" />
                  &lt;el-option label="进货数据" value="purchase" />
                  &lt;el-option label="退货数据" value="returns" />
                &lt;/el-select>
              &lt;/el-form-item>
              
              &lt;el-form-item label="数据文件">
                &lt;el-select 
                  v-model="dataSourceForm.fileId" 
                  placeholder="选择已上传的数据文件"
                  @change="loadFilePreview"
                >
                  &lt;el-option 
                    v-for="file in uploadedFiles" 
                    :key="file.id" 
                    :label="file.fileName" 
                    :value="file.id" 
                  />
                &lt;/el-select>
              &lt;/el-form-item>
            &lt;/el-form>
          &lt;/el-collapse-item>

          &lt;el-collapse-item title="清洗规则配置" name="cleaningRules">
            &lt;el-form :model="cleaningRulesForm" label-width="120px">
              &lt;h4>缺失值处理&lt;/h4>
              &lt;el-form-item 
                v-for="field in availableFields" 
                :key="field.name" 
                :label="field.label"
              >
                &lt;el-select 
                  v-model="cleaningRulesForm.missingValues[field.name]" 
                  placeholder="选择处理方式"
                >
                  &lt;el-option label="忽略" value="ignore" />
                  &lt;el-option label="删除行" value="drop" />
                  &lt;el-option label="填充零值" value="fill_zero" />
                  &lt;el-option label="填充平均值" value="fill_mean" />
                  &lt;el-option label="填充中位数" value="fill_median" />
                  &lt;el-option label="填充众数" value="fill_mode" />
                  &lt;el-option label="前值填充" value="fill_forward" />
                  &lt;el-option label="后值填充" value="fill_backward" />
                &lt;/el-select>
              &lt;/el-form-item>

              &lt;h4>异常值处理&lt;/h4>
              &lt;el-form-item label="检测方法">
                &lt;el-select v-model="cleaningRulesForm.outlierDetection.method">
                  &lt;el-option label="Z-分数法" value="zscore" />
                  &lt;el-option label="IQR法" value="iqr" />
                  &lt;el-option label="标准差法" value="std_dev" />
                  &lt;el-option label="不处理" value="none" />
                &lt;/el-select>
              &lt;/el-form-item>

              &lt;el-form-item label="阈值" v-if="cleaningRulesForm.outlierDetection.method !== 'none'">
                &lt;el-input-number 
                  v-model="cleaningRulesForm.outlierDetection.threshold" 
                  :min="1" 
                  :max="10" 
                  :step="0.5"
                />
              &lt;/el-form-item>

              &lt;el-form-item label="处理方式" v-if="cleaningRulesForm.outlierDetection.method !== 'none'">
                &lt;el-select v-model="cleaningRulesForm.outlierDetection.action">
                  &lt;el-option label="标记" value="flag" />
                  &lt;el-option label="删除" value="remove" />
                  &lt;el-option label="替换为边界值" value="cap" />
                  &lt;el-option label="替换为均值" value="mean" />
                &lt;/el-select>
              &lt;/el-form-item>

              &lt;h4>数据格式化&lt;/h4>
              &lt;el-form-item label="日期格式">
                &lt;el-select v-model="cleaningRulesForm.formatting.dateFormat">
                  &lt;el-option label="YYYY-MM-DD" value="YYYY-MM-DD" />
                  &lt;el-option label="MM/DD/YYYY" value="MM/DD/YYYY" />
                  &lt;el-option label="DD/MM/YYYY" value="DD/MM/YYYY" />
                  &lt;el-option label="YYYY/MM/DD" value="YYYY/MM/DD" />
                &lt;/el-select>
              &lt;/el-form-item>

              &lt;el-form-item label="数值精度">
                &lt;el-input-number 
                  v-model="cleaningRulesForm.formatting.numberPrecision" 
                  :min="0" 
                  :max="6" 
                  :step="1"
                />
              &lt;/el-form-item>
            &lt;/el-form>
          &lt;/el-collapse-item>

          &lt;el-collapse-item title="自定义规则" name="customRules">
            &lt;el-button size="small" @click="addCustomRule">添加规则&lt;/el-button>
            
            &lt;div 
              v-for="(rule, index) in cleaningRulesForm.customRules" 
              :key="index" 
              class="custom-rule-item"
            >
              &lt;el-row :gutter="10">
                &lt;el-col :span="6">
                  &lt;el-select 
                    v-model="rule.field" 
                    placeholder="选择字段"
                    style="width: 100%"
                  >
                    &lt;el-option 
                      v-for="field in availableFields" 
                      :key="field.name" 
                      :label="field.label" 
                      :value="field.name" 
                    />
                  &lt;/el-select>
                &lt;/el-col>
                
                &lt;el-col :span="6">
                  &lt;el-select 
                    v-model="rule.operation" 
                    placeholder="选择操作"
                    style="width: 100%"
                  >
                    &lt;el-option label="替换值" value="replace" />
                    &lt;el-option label="过滤条件" value="filter" />
                    &lt;el-option label="转换格式" value="transform" />
                  &lt;/el-select>
                &lt;/el-col>
                
                &lt;el-col :span="6">
                  &lt;el-input 
                    v-model="rule.value" 
                    placeholder="条件值"
                  />
                &lt;/el-col>
                
                &lt;el-col :span="4">
                  &lt;el-input 
                    v-model="rule.replacement" 
                    placeholder="替换值"
                    v-if="rule.operation === 'replace'"
                  />
                &lt;/el-col>
                
                &lt;el-col :span="2">
                  &lt;el-button 
                    type="danger" 
                    icon="Delete" 
                    circle 
                    @click="removeCustomRule(index)"
                  />
                &lt;/el-col>
              &lt;/el-row>
            &lt;/div>
          &lt;/el-collapse-item>
        &lt;/el-collapse>
      &lt;/div>

      &lt;div class="data-preview" v-loading="loading">
        &lt;el-tabs v-model="activeTab" type="card">
          &lt;el-tab-pane label="数据预览" name="preview">
            &lt;div class="preview-header">
              &lt;el-radio-group v-model="previewType" size="small">
                &lt;el-radio-button label="original">原始数据&lt;/el-radio-button>
                &lt;el-radio-button label="cleaned" :disabled="!hasCleanedData">清洗后数据&lt;/el-radio-button>
                &lt;el-radio-button label="diff" :disabled="!hasCleanedData">差异对比&lt;/el-radio-button>
              &lt;/el-radio-group>
              
              &lt;el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                layout="sizes, prev, pager, next"
                :total="totalRows"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            &lt;/div>

            &lt;el-table
              :data="previewData"
              border
              stripe
              style="width: 100%"
              max-height="400"
              :row-class-name="getRowClassName"
            >
              &lt;el-table-column
                v-for="column in tableColumns"
                :key="column.prop"
                :prop="column.prop"
                :label="column.label"
                :width="column.width"
                :sortable="column.sortable"
              >
                &lt;template #default="scope">
                  &lt;div :class="getCellClassName(scope.row, column.prop)">
                    {{ scope.row[column.prop] }}
                  &lt;/div>
                &lt;/template>
              &lt;/el-table-column>
            &lt;/el-table>
          &lt;/el-tab-pane>
          
          &lt;el-tab-pane label="清洗统计" name="stats" :disabled="!hasCleanedData">
            &lt;el-row :gutter="20">
              &lt;el-col :span="6">
                &lt;el-statistic title="总记录数" :value="statistics.totalRecords" />
              &lt;/el-col>
              &lt;el-col :span="6">
                &lt;el-statistic title="修改记录数" :value="statistics.modifiedRecords" />
              &lt;/el-col>
              &lt;el-col :span="6">
                &lt;el-statistic title="删除记录数" :value="statistics.deletedRecords" />
              &lt;/el-col>
              &lt;el-col :span="6">
                &lt;el-statistic title="异常值数量" :value="statistics.outlierCount" />
              &lt;/el-col>
            &lt;/el-row>
            
            &lt;div class="stats-charts">
              &lt;div class="chart-container">
                &lt;h4>字段缺失值统计&lt;/h4>
                &lt;div ref="missingValueChart" style="height: 300px">&lt;/div>
              &lt;/div>
              
              &lt;div class="chart-container">
                &lt;h4>异常值分布&lt;/h4>
                &lt;div ref="outlierChart" style="height: 300px">&lt;/div>
              &lt;/div>
            &lt;/div>
          &lt;/el-tab-pane>
        &lt;/el-tabs>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'

// 状态变量
const activeCollapse = ref(['dataSource', 'cleaningRules'])
const activeTab = ref('preview')
const loading = ref(false)
const processing = ref(false)
const previewType = ref('original')
const hasCleanedData = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalRows = ref(0)
const uploadedFiles = ref([])
const availableFields = ref([])
const tableColumns = ref([])
const previewData = ref([])
const originalData = ref([])
const cleanedData = ref([])
const missingValueChart = ref(null)
const outlierChart = ref(null)

// 表单数据
const dataSourceForm = reactive({
  dataType: 'sales',
  fileId: ''
})

const cleaningRulesForm = reactive({
  missingValues: {},
  outlierDetection: {
    method: 'zscore',
    threshold: 3,
    action: 'flag'
  },
  formatting: {
    dateFormat: 'YYYY-MM-DD',
    numberPrecision: 2
  },
  customRules: []
})

// 统计数据
const statistics = reactive({
  totalRecords: 0,
  modifiedRecords: 0,
  deletedRecords: 0,
  outlierCount: 0,
  missingValueStats: {},
  outlierDistribution: {}
})

// 加载上传文件列表
const loadUploadedFiles = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/data-import/files')
    uploadedFiles.value = response.data
  } catch (error) {
    ElMessage.error('获取上传文件列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 加载文件预览
const loadFilePreview = async () => {
  if (!dataSourceForm.fileId) return
  
  try {
    loading.value = true
    const response = await axios.get(`/api/data-import/files/${dataSourceForm.fileId}/preview`)
    
    // 设置可用字段
    availableFields.value = response.data.columns.map(col => ({
      name: col.field,
      label: col.title,
      type: col.dataType
    }))
    
    // 设置表格列
    tableColumns.value = response.data.columns.map(col => ({
      prop: col.field,
      label: col.title,
      width: col.width || '',
      sortable: true
    }))
    
    // 设置原始数据
    originalData.value = response.data.data
    totalRows.value = response.data.totalRows
    
    // 重置清洗后数据
    cleanedData.value = []
    hasCleanedData.value = false
    
    // 更新预览数据
    updatePreviewData()
    
    // 初始化缺失值处理配置
    availableFields.value.forEach(field => {
      if (!cleaningRulesForm.missingValues[field.name]) {
        cleaningRulesForm.missingValues[field.name] = 'ignore'
      }
    })
  } catch (error) {
    ElMessage.err