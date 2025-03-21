&lt;template>
  &lt;div class="data-import-page">
    &lt;el-page-header content="数据导入" @back="goBack">
      &lt;template #extra>
        &lt;el-button-group>
          &lt;el-button type="primary" :icon="Document" @click="showTemplates">
            模板管理
          &lt;/el-button>
          &lt;el-button type="info" :icon="InfoFilled" @click="showHelp">
            使用帮助
          &lt;/el-button>
        &lt;/el-button-group>
      &lt;/template>
    &lt;/el-page-header>

    &lt;el-row :gutter="20" class="main-content">
      &lt;el-col :span="24">
        &lt;!-- 步骤导航 -->
        &lt;el-steps :active="currentStep" finish-status="success" simple>
          &lt;el-step title="选择模板" />
          &lt;el-step title="上传文件" />
          &lt;el-step title="验证数据" />
          &lt;el-step title="导入数据" />
          &lt;el-step title="导入完成" />
        &lt;/el-steps>
      &lt;/el-col>

      &lt;!-- 步骤1: 选择模板 -->
      &lt;el-col :span="24" v-if="currentStep === 0">
        &lt;excel-template-download @template-selected="handleTemplateSelected" />
        &lt;div class="step-actions">
          &lt;el-button type="primary" @click="nextStep" :disabled="!selectedTemplate">
            下一步
          &lt;/el-button>
        &lt;/div>
      &lt;/el-col>

      &lt;!-- 步骤2: 上传文件 -->
      &lt;el-col :span="24" v-else-if="currentStep === 1">
        &lt;file-uploader
          :upload-url="uploadUrl"
          @file-uploaded="handleFileUploaded"
          @upload-failed="handleUploadFailed"
          @reset="handleReset"
        />
        &lt;div class="step-actions">
          &lt;el-button @click="prevStep">上一步&lt;/el-button>
        &lt;/div>
      &lt;/el-col>

      &lt;!-- 步骤3: 验证数据 -->
      &lt;el-col :span="24" v-else-if="currentStep === 2">
        &lt;data-validation-feedback
          :summary="validationSummary"
          :errors="validationErrors"
          :warnings="validationWarnings"
          @proceed="handleProceedToImport"
          @cancel="handleCancelImport"
          @fix-applied="handleFixApplied"
          @warning-ignored="handleWarningIgnored"
        />
        &lt;div class="step-actions">
          &lt;el-button @click="prevStep">上一步&lt;/el-button>
        &lt;/div>
      &lt;/el-col>

      &lt;!-- 步骤4: 导入数据 -->
      &lt;el-col :span="24" v-else-if="currentStep === 3 || currentStep === 4">
        &lt;import-progress-tracker
          :step="importStep"
          :status="importStatus"
          :progress="importProgress"
          :stats="importStats"
          :current-operation="currentOperation"
          :error-message="errorMessage"
          :completion-status="completionStatus"
          @proceed="handleProceedImport"
          @cancel="handleCancelImport"
          @view-results="handleViewResults"
          @new-import="resetImport"
        />
      &lt;/el-col>
    &lt;/el-row>

    &lt;!-- 帮助对话框 -->
    &lt;el-dialog v-model="helpDialogVisible" title="数据导入帮助" width="60%">
      &lt;div class="help-content">
        &lt;h3>数据导入流程&lt;/h3>
        &lt;ol>
          &lt;li>&lt;strong>选择模板：&lt;/strong>根据需要导入的数据类型选择并下载对应的Excel模板。&lt;/li>
          &lt;li>&lt;strong>填写数据：&lt;/strong>按照模板格式填写数据，确保格式正确。&lt;/li>
          &lt;li>&lt;strong>上传文件：&lt;/strong>将填写好的Excel文件上传到系统。&lt;/li>
          &lt;li>&lt;strong>验证数据：&lt;/strong>系统会自动验证数据格式和内容，并提示错误和警告。&lt;/li>
          &lt;li>&lt;strong>修复问题：&lt;/strong>根据系统提示修复数据问题或使用系统提供的修复建议。&lt;/li>
          &lt;li>&lt;strong>导入数据：&lt;/strong>验证通过后，系统会将数据导入到数据库。&lt;/li>
        &lt;/ol>

        &lt;h3>注意事项&lt;/h3>
        &lt;ul>
          &lt;li>请使用系统提供的标准模板，不要修改模板格式。&lt;/li>
          &lt;li>日期格式必须为YYYY-MM-DD，例如：2024-03-21。&lt;/li>
          &lt;li>数字字段不要包含特殊字符，如货币符号。&lt;/li>
          &lt;li>导入的商品编码必须与系统中已有商品编码一致。&lt;/li>
          &lt;li>文件大小不能超过10MB。&lt;/li>
        &lt;/ul>

        &lt;h3>常见问题&lt;/h3>
        &lt;el-collapse>
          &lt;el-collapse-item title="导入失败怎么办？" name="1">
            &lt;p>导入失败通常是由于数据格式不正确或缺少必要字段导致的。请检查系统提供的错误信息，修复相应问题后重新尝试。&lt;/p>
          &lt;/el-collapse-item>
          &lt;el-collapse-item title="如何处理警告？" name="2">
            &lt;p>警告表示数据可能存在问题但不会阻止导入。您可以选择忽略警告或根据系统建议修复问题。&lt;/p>
          &lt;/el-collapse-item>
          &lt;el-collapse-item title="是否可以部分导入数据？" name="3">
            &lt;p>不可以。为保证数据一致性，系统只支持全部导入或全部不导入。如果存在错误，需要全部修复后才能导入。&lt;/p>
          &lt;/el-collapse-item>
        &lt;/el-collapse>
      &lt;/div>
    &lt;/el-dialog>

    &lt;!-- 模板管理对话框 -->
    &lt;el-dialog v-model="templatesDialogVisible" title="数据模板管理" width="70%">
      &lt;excel-template-download />
    &lt;/el-dialog>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Document, InfoFilled } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import ExcelTemplateDownload from '@/components/data-import/ExcelTemplateDownload.vue';
import FileUploader from '@/components/data-import/FileUploader.vue';
import DataValidationFeedback from '@/components/data-import/DataValidationFeedback.vue';
import ImportProgressTracker from '@/components/data-import/ImportProgressTracker.vue';

export default {
  name: 'DataImport',
  components: {
    ExcelTemplateDownload,
    FileUploader,
    DataValidationFeedback,
    ImportProgressTracker
  },
  setup() {
    const router = useRouter();
    
    // 步骤控制
    const currentStep = ref(0);
    const selectedTemplate = ref(null);
    
    // 文件上传
    const uploadUrl = '/api/data-import/upload';
    const uploadedFile = ref(null);
    const uploadOptions = ref(null);
    
    // 数据验证
    const validationSummary = reactive({
      totalRecords: 0,
      validRecords: 0,
      errorRecords: 0,
      warningRecords: 0
    });
    const validationErrors = ref([]);
    const validationWarnings = ref([]);
    
    // 导入进度
    const importStep = ref(0); // 0: 验证, 1: 导入, 2: 完成
    const importStatus = ref('idle');
    const importProgress = ref(0);
    const importStats = reactive({
      totalRecords: 0,
      successRecords: 0,
      failedRecords: 0
    });
    const currentOperation = ref('');
    const errorMessage = ref('');
    const completionStatus = ref('success');
    
    // 对话框控制
    const helpDialogVisible = ref(false);
    const templatesDialogVisible = ref(false);

    // 返回上一页
    const goBack = () => {
      router.go(-1);
    };

    // 显示帮助
    const showHelp = () => {
      helpDialogVisible.value = true;
    };

    // 显示模板管理
    const showTemplates = () => {
      templatesDialogVisible.value = true;
    };

    // 下一步
    const nextStep = () => {
      currentStep.value++;
    };

    // 上一步
    const prevStep = () => {
      currentStep.value--;
    };

    // 处理模板选择
    const handleTemplateSelected = (template) => {
      selectedTemplate.value = template;
    };

    // 处理文件上传成功
    const handleFileUploaded = async (result) => {
      uploadedFile.value = result.file;
      uploadOptions.value = result.options;
      
      // 模拟验证过程
      importStatus.value = 'validating';
      importProgress.value = 0;
      currentOperation.value = '正在验证数据...';
      
      try {
        // 模拟异步验证过程
        await simulateValidation();
        
        // 更新验证结果
        validationSummary.totalRecords = 100;
        validationSummary.validRecords = 95;
        validationSummary.errorRecords = 2;
        validationSummary.warningRecords = 3;
        
        // 模拟错误和警告
        validationErrors.value = [
          {
            row: 5,
            column: '日期',
            value: '2024/03/21',
            message: '日期格式不正确，应为YYYY-MM-DD格式',
            type: 'date_format'
          },
          {
            row: 12,
            column: '销售数量',
            value: '-5',
            message: '销售数量不能为负数',
            type: 'number_format'
          }
        ];
        
        validationWarnings.value = [
          {
            row: 8,
            column: '销售金额',
            value: '1000',
            message: '销售金额异常高，请确认是否正确',
            type: 'value_anomaly'
          },
          {
            row: 15,
            column: '折扣金额',
            value: '',
            message: '折扣金额为空，将使用默认值0',
            type: 'missing_value'
          },
          {
            row: 23,
            column: '商品编码',
            value: 'PRD-99999',
            message: '商品编码不存在于系统中',
            type: 'invalid_reference'
          }
        ];
        
        // 进入验证结果步骤
        currentStep.value = 2;
      } catch (error) {
        ElMessage.error('数据验证失败: ' + error.message);
      }
    };

    // 处理上传失败
    const handleUploadFailed = (error) => {
      ElMessage.error('文件上传失败: ' + error.message);
    };

    // 处理重置
    const handleReset = () => {
      uploadedFile.value = null;
      uploadOptions.value = null;
    };

    // 处理继续导入
    const handleProceedToImport = () => {
      currentStep.value = 3;
      importStep.value = 1; // 导入步骤
      startImport();
    };

    // 处理取消导入
    const handleCancelImport = () => {
      ElMessageBox.confirm('确定要取消导入吗？已上传的数据将不会保存。', '取消导入', {
        confirmButtonText: '确定',
        cancelButtonText: '返回',
        type: 'warning'
      }).then(() => {
        resetImport();
      }).catch(() => {
        // 用户取消操作，不做任何处理
      });
    };

    // 处理修复应用
    const handleFixApplied = ({ issue, fix }) => {
      ElMessage.success(`已应用修复: ${issue.column} 在第 ${issue.row} 行`);
      
      // 更新错误或警告列表
      if (issue.type === 'error') {
        validationErrors.value = validationErrors.value.filter(e => 
          !(e.row === issue.row && e.column === issue.column)
        );
        validationSummary.errorRecords--;
        validationSummary.validRecords++;
      } else {
        validationWarnings.value = validationWarnings.value.filter(w => 
          !(w.row === issue.row && w.column === issue.column)
        );
        validationSummary.warningRecords--;
      }
    };

    // 处理警告忽略
    const handleWarningIgnored = (warning) => {
      ElMessage.info(`已忽略警告: ${warning.column} 在第 ${warning.row} 行`);
      
      // 从警告列表中移除
      validationWarnings.value = validationWarnings.value.filter(w => 
        !(w.row === warning.row && w.column === warning.column)
      );
      validationSummary.warningRecords--;
    };

    // 开始导入
    const startImport = async () => {
      importStatus.value = 'importing';
      importProgress.value = 0;
      currentOperation.value = '正在导入数据...';
      
      try {
        // 模拟导入过程
        await simulateImport();
        
        // 更新导入统计
        importStats.totalRecords = validationSummary.totalRecords;
        importStats.successRecords = validationSummary.validRecords;
        importStats.failedRecords = 0;
        
        // 设置完成状态
        importStatus.value = 'completed';
        importStep.value = 2; // 完成步骤
        currentStep.value = 4;
        completionStatus.value = 'success';
      } catch (error) {
        importStatus.value = 'error';
        errorMessage.value = '导入过程中发生错误: ' + error.message;
        completionStatus.value = 'failed';
      }
    };

    // 处理继续导入
    const handleProceedImport = () => {
      if (importStep.value === 0) {
        // 开始验证
        importStatus.value = 'validating';
        importProgress.value = 0;
        currentOperation.value = '正在验证数据...';
      } else if (importStep.value === 1) {
        // 开始导入
        startImport();
      }
    };

    // 处理查看结果
    const handleViewResults = () => {
      // 跳转到导入结果页面或显示结果对话框
      ElMessage.success('导入完成，共导入 ' + importStats.successRecords + ' 条记录');
    };

    // 重置导入
    const resetImport = () => {
      currentStep.value = 0;
      selectedTemplate.value = null;
      uploadedFile.value = null;
      uploadOptions.value = null;
      
      validationSummary.totalRecords = 0;
      validationSummary.validRecords = 0;
      validationSummary.errorRecords = 0;
      validationSummary.warningRecords = 0;
      
      validationErrors.value = [];
      validationWarnings.value = [];
      
      importStep.value = 0;
      importStatus.value = 'idle';
      importProgress.value = 0;
      
      importStats.totalRecords = 0;
      importStats.successRecords = 0;
      importStats.failedRecords = 0;
      
      currentOperation.value = '';
      errorMessage.value = '';
      completionStatus.value = 'success';
    };

    // 模拟验证过程
    const simulateValidation = () => {
      return new Promise((resolve) => {
        let progress = 0;
        const interval = setInterval(() => {
          progress += 10;
          importProgress.value = progress;
          
          if (progress >= 100) {
            clearInterval(interval);
            resolve();
          }
        }, 300);
      });
    };

    // 模拟导入过程
    const simulateImport = () => {
      return new Promise((resolve) => {
        let progress = 0;
        const interval = setInterval(() => {
          progress += 5;
          importProgress.value = progress;
          
          // 更新当前操作
          if (progress < 30) {
            currentOperation.value = '正在准备数据...';
          } else if (progress < 60) {
            currentOperation.value = '正在写入数据库...';
          } else if (progress < 90) {
            currentOperation.value = '正在更新索引...';
          } else {
            currentOperation.value = '正在完成导入...';
          }
          
          // 更新导入统计
          importStats.totalRecords = validationSummary.totalRecords;
          importStats.successRecords = Math.floor((validationSummary.validRecords * progress) / 100);
          
          if (progress >= 100) {
            clearInterval(interval);
            importStats.successRecords = validationSummary.validRecords;
            resolve();
          }
        }, 200);
      });
    };

    return {
      // 数据
      currentStep,
      selectedTemplate,
      uploadUrl,
      validationSummary,
      validationErrors,
      validationWarnings,
      importStep,
      importStatus,
      importProgress,
      importStats,
      currentOperation,
      errorMessage,
      completionStatus,
      helpDialogVisible,
      templatesDialogVisible,
      
      // 方法
      goBack,
      showHelp,
      showTemplates,
      nextStep,
      prevStep,
      handleTemplateSelected,
      handleFileUploaded,
      handleUploadFailed,
      handleReset,
      handleProceedToImport,
      handleCancelImport,
      handleFixApplied,
      handleWarningIgnored,
      handleProceedImport,
      handleViewResults,
      resetImport,
      
      // 图标
      Document,
      InfoFilled
    };
  }
};
&lt;/script>

&lt;style scoped>
.data-import-page {
  padding: 20px;
}

.main-content {
  margin-top: 30px;
}

.step-actions {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.help-content {
  h3 {
    margin-top: 20px;
    margin-bottom: 10px;
    color: #303133;
  }

  ol, ul {
    padding-left: 20px;
    margin: 10px 0;
    color: #606266;
    line-height: 1.6;
  }

  li {
    margin-bottom: 8px;
  }
}
&lt;/style>