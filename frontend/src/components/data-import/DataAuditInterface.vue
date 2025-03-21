<template>
  <div class="data-audit-interface">
    <!-- 文件上传区域 -->
    <el-card class="audit-section">
      <template #header>
        <div class="card-header">
          <span>数据审核</span>
          <el-button type="primary" @click="showRules">查看审核规则</el-button>
        </div>
      </template>
      
      <el-form :model="auditForm" label-width="120px">
        <el-form-item label="导入类型">
          <el-select v-model="auditForm.importType" placeholder="选择导入类型">
            <el-option label="销售数据" value="SALES" />
            <el-option label="库存数据" value="INVENTORY" />
            <el-option label="商品数据" value="PRODUCT" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="上传文件">
          <el-upload
            class="upload-demo"
            :action="uploadUrl"
            :headers="headers"
            :data="uploadData"
            :before-upload="beforeUpload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :auto-upload="false"
            ref="upload"
          >
            <template #trigger>
              <el-button type="primary">选择文件</el-button>
            </template>
            <el-button class="ml-3" type="success" @click="submitUpload">
              开始审核
            </el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 审核结果展示区域 -->
    <el-card v-if="auditReport" class="audit-section mt-4">
      <template #header>
        <div class="card-header">
          <span>审核报告</span>
          <div class="audit-summary">
            <el-tag type="danger" v-if="auditReport.summary.critical_issues">
              严重问题: {{ auditReport.summary.critical_issues }}
            </el-tag>
            <el-tag type="warning" v-if="auditReport.summary.warnings">
              警告: {{ auditReport.summary.warnings }}
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 完整性检查结果 -->
      <div class="audit-result-section">
        <h3>数据完整性检查</h3>
        <el-descriptions border>
          <el-descriptions-item label="总行数">
            {{ auditReport.completeness.total_rows }}
          </el-descriptions-item>
          <el-descriptions-item label="完整记录数">
            {{ auditReport.completeness.complete_rows }}
          </el-descriptions-item>
          <el-descriptions-item label="缺失字段" :span="2">
            <el-tag 
              v-for="field in auditReport.completeness.missing_fields" 
              :key="field"
              type="danger"
              class="mx-1"
            >
              {{ field }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 空值统计 -->
        <div v-if="Object.keys(auditReport.completeness.null_counts).length > 0">
          <h4>空值统计</h4>
          <el-table :data="nullCountsData" border stripe>
            <el-table-column prop="field" label="字段" />
            <el-table-column prop="count" label="空值数量" />
            <el-table-column prop="percentage" label="占比">
              <template #default="scope">
                {{ scope.row.percentage }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 一致性检查结果 -->
      <div class="audit-result-section">
        <h3>数据一致性检查</h3>
        <el-descriptions border>
          <el-descriptions-item label="重复记录">
            {{ auditReport.consistency.duplicate_records }}
          </el-descriptions-item>
          <el-descriptions-item label="负值记录" :span="2">
            <div v-for="(count, field) in auditReport.consistency.negative_values" :key="field">
              {{ field }}: {{ count }}
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 准确性检查结果 -->
      <div class="audit-result-section">
        <h3>数据准确性检查</h3>
        <div v-if="Object.keys(auditReport.accuracy.outliers).length > 0">
          <h4>异常值统计</h4>
          <el-table :data="outliersData" border stripe>
            <el-table-column prop="field" label="字段" />
            <el-table-column prop="count" label="异常值数量" />
            <el-table-column prop="suggestion" label="建议" />
          </el-table>
        </div>
      </div>

      <!-- 修复建议 -->
      <div class="audit-result-section">
        <h3>修复建议</h3>
        <el-timeline>
          <el-timeline-item
            v-for="(suggestion, index) in auditReport.summary.suggestions"
            :key="index"
            :type="suggestion.includes('严重') ? 'danger' : 'warning'"
          >
            {{ suggestion }}
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- 审核规则对话框 -->
    <el-dialog
      v-model="rulesDialogVisible"
      title="数据审核规则"
      width="50%"
    >
      <div v-if="currentRules">
        <h4>必填字段</h4>
        <el-tag
          v-for="field in currentRules.required_fields"
          :key="field"
          class="mx-1"
        >
          {{ field }}
        </el-tag>

        <h4 class="mt-4">数据类型要求</h4>
        <el-descriptions border>
          <el-descriptions-item
            v-for="(type, field) in currentRules.data_types"
            :key="field"
            :label="field"
          >
            {{ type }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 class="mt-4">数据约束</h4>
        <el-descriptions border>
          <el-descriptions-item
            v-for="(constraint, field) in currentRules.constraints"
            :key="field"
            :label="field"
          >
            {{ constraint }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import axios from 'axios'

export default {
  name: 'DataAuditInterface',
  setup() {
    const store = useStore()
    const auditForm = ref({
      importType: 'SALES'
    })
    const auditReport = ref(null)
    const rulesDialogVisible = ref(false)
    const currentRules = ref(null)
    const upload = ref(null)

    // 计算上传URL
    const uploadUrl = computed(() => {
      return `${store.state.apiBaseUrl}/audit/upload`
    })

    // 计算上传请求头
    const headers = computed(() => {
      return {
        Authorization: `Bearer ${store.state.auth.token}`
      }
    })

    // 计算上传数据
    const uploadData = computed(() => {
      return {
        import_type: auditForm.value.importType
      }
    })

    // 计算空值统计数据
    const nullCountsData = computed(() => {
      if (!auditReport.value) return []
      return Object.entries(auditReport.value.completeness.null_counts).map(([field, count]) => ({
        field,
        count,
        percentage: ((count / auditReport.value.completeness.total_rows) * 100).toFixed(2)
      }))
    })

    // 计算异常值统计数据
    const outliersData = computed(() => {
      if (!auditReport.value) return []
      return Object.entries(auditReport.value.accuracy.outliers).map(([field, count]) => ({
        field,
        count,
        suggestion: count > 0 ? '建议检查这些异常值' : '无异常'
      }))
    })

    // 上传前的处理
    const beforeUpload = (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                      file.type === 'application/vnd.ms-excel'
      if (!isExcel) {
        ElMessage.error('只能上传Excel文件!')
        return false
      }
      return true
    }

    // 提交上传
    const submitUpload = () => {
      upload.value.submit()
    }

    // 上传成功的处理
    const handleUploadSuccess = (response) => {
      if (response.status === 'success') {
        auditReport.value = response.data.audit_report
        ElMessage.success('文件审核完成')
      } else {
        ElMessage.error(response.message || '审核失败')
      }
    }

    // 上传失败的处理
    const handleUploadError = (error) => {
      ElMessage.error('文件上传失败: ' + error.message)
    }

    // 显示审核规则
    const showRules = async () => {
      try {
        const response = await axios.post(
          `${store.state.apiBaseUrl}/audit/rules`,
          { import_type: auditForm.value.importType },
          { headers: headers.value }
        )
        if (response.data.status === 'success') {
          currentRules.value = response.data.data.rules
          rulesDialogVisible.value = true
        }
      } catch (error) {
        ElMessage.error('获取审核规则失败: ' + error.message)
      }
    }

    return {
      auditForm,
      auditReport,
      rulesDialogVisible,
      currentRules,
      upload,
      uploadUrl,
      headers,
      uploadData,
      nullCountsData,
      outliersData,
      beforeUpload,
      submitUpload,
      handleUploadSuccess,
      handleUploadError,
      showRules
    }
  }
}
</script>

<style scoped>
.data-audit-interface {
  padding: 20px;
}

.audit-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audit-summary {
  display: flex;
  gap: 10px;
}

.audit-result-section {
  margin-top: 20px;
  padding: 15px;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.audit-result-section h3 {
  margin-bottom: 15px;
  color: #303133;
}

.audit-result-section h4 {
  margin: 15px 0 10px;
  color: #606266;
}

.mx-1 {
  margin: 0 5px;
}

.mt-4 {
  margin-top: 20px;
}

.el-timeline-item {
  padding-bottom: 20px;
}
</style>