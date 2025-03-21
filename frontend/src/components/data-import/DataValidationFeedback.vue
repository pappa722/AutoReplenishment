&lt;template>
  &lt;div class="data-validation-feedback">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>数据验证结果&lt;/span>
          &lt;el-tag :type="validationStatus.type" size="small">
            {{ validationStatus.text }}
          &lt;/el-tag>
        &lt;/div>
      &lt;/template>

      &lt;div class="validation-summary" v-if="summary">
        &lt;el-descriptions border>
          &lt;el-descriptions-item label="总记录数">
            {{ summary.totalRecords }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="有效记录">
            {{ summary.validRecords }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="错误记录">
            &lt;span class="error-count">{{ summary.errorRecords }}&lt;/span>
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="警告记录">
            &lt;span class="warning-count">{{ summary.warningRecords }}&lt;/span>
          &lt;/el-descriptions-item>
        &lt;/el-descriptions>
      &lt;/div>

      &lt;div class="validation-details" v-if="errors.length || warnings.length">
        &lt;el-tabs v-model="activeTab">
          &lt;el-tab-pane label="错误" name="errors" v-if="errors.length">
            &lt;el-table :data="errors" border style="width: 100%">
              &lt;el-table-column prop="row" label="行号" width="80" />
              &lt;el-table-column prop="column" label="列名" width="120" />
              &lt;el-table-column prop="value" label="错误值" width="150" />
              &lt;el-table-column prop="message" label="错误说明" />
              &lt;el-table-column label="操作" width="120">
                &lt;template #default="scope">
                  &lt;el-button
                    type="primary"
                    link
                    @click="handleErrorFix(scope.row)"
                  >
                    修复建议
                  &lt;/el-button>
                &lt;/template>
              &lt;/el-table-column>
            &lt;/el-table>
          &lt;/el-tab-pane>

          &lt;el-tab-pane label="警告" name="warnings" v-if="warnings.length">
            &lt;el-table :data="warnings" border style="width: 100%">
              &lt;el-table-column prop="row" label="行号" width="80" />
              &lt;el-table-column prop="column" label="列名" width="120" />
              &lt;el-table-column prop="value" label="警告值" width="150" />
              &lt;el-table-column prop="message" label="警告说明" />
              &lt;el-table-column label="操作" width="180">
                &lt;template #default="scope">
                  &lt;el-button
                    type="warning"
                    link
                    @click="handleWarningIgnore(scope.row)"
                  >
                    忽略警告
                  &lt;/el-button>
                  &lt;el-button
                    type="primary"
                    link
                    @click="handleWarningFix(scope.row)"
                  >
                    修复建议
                  &lt;/el-button>
                &lt;/template>
              &lt;/el-table-column>
            &lt;/el-table>
          &lt;/el-tab-pane>
        &lt;/el-tabs>
      &lt;/div>

      &lt;div class="validation-actions" v-if="showActions">
        &lt;el-divider />
        &lt;div class="action-buttons">
          &lt;el-button
            type="primary"
            :disabled="!canProceed"
            @click="handleProceed"
          >
            继续导入
          &lt;/el-button>
          &lt;el-button @click="handleCancel">取消导入&lt;/el-button>
        &lt;/div>
      &lt;/div>
    &lt;/el-card>

    &lt;!-- 修复建议对话框 -->
    &lt;el-dialog
      v-model="fixDialogVisible"
      :title="fixDialogTitle"
      width="50%"
    >
      &lt;div v-if="selectedIssue" class="fix-suggestions">
        &lt;p class="issue-description">
          &lt;el-icon>&lt;Warning />&lt;/el-icon>
          {{ selectedIssue.message }}
        &lt;/p>

        &lt;h4>修复建议：&lt;/h4>
        &lt;el-radio-group v-model="selectedFix" class="fix-options">
          &lt;el-radio
            v-for="(fix, index) in fixSuggestions"
            :key="index"
            :label="index"
            border
          >
            {{ fix.description }}
          &lt;/el-radio>
        &lt;/el-radio-group>

        &lt;div class="fix-preview" v-if="selectedFix !== null">
          &lt;h4>修复后的值：&lt;/h4>
          &lt;el-alert
            :title="fixSuggestions[selectedFix].preview"
            type="success"
            :closable="false"
          />
        &lt;/div>
      &lt;/div>
      &lt;template #footer>
        &lt;span class="dialog-footer">
          &lt;el-button @click="fixDialogVisible = false">取消&lt;/el-button>
          &lt;el-button
            type="primary"
            @click="applyFix"
            :disabled="selectedFix === null"
          >
            应用修复
          &lt;/el-button>
        &lt;/span>
      &lt;/template>
    &lt;/el-dialog>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref, computed } from 'vue';
import { Warning } from '@element-plus/icons-vue';

export default {
  name: 'DataValidationFeedback',
  props: {
    // 验证结果摘要
    summary: {
      type: Object,
      required: true
    },
    // 错误列表
    errors: {
      type: Array,
      default: () => []
    },
    // 警告列表
    warnings: {
      type: Array,
      default: () => []
    },
    // 是否显示操作按钮
    showActions: {
      type: Boolean,
      default: true
    }
  },
  emits: ['proceed', 'cancel', 'fix-applied', 'warning-ignored'],
  setup(props, { emit }) {
    const activeTab = ref('errors');
    const fixDialogVisible = ref(false);
    const selectedIssue = ref(null);
    const selectedFix = ref(null);
    const fixDialogType = ref('error');

    // 计算验证状态
    const validationStatus = computed(() => {
      if (props.errors.length > 0) {
        return { type: 'danger', text: '验证失败' };
      }
      if (props.warnings.length > 0) {
        return { type: 'warning', text: '需要确认' };
      }
      return { type: 'success', text: '验证通过' };
    });

    // 计算是否可以继续
    const canProceed = computed(() => {
      return props.errors.length === 0;
    });

    // 计算对话框标题
    const fixDialogTitle = computed(() => {
      return fixDialogType.value === 'error' ? '错误修复建议' : '警告修复建议';
    });

    // 修复建议列表
    const fixSuggestions = computed(() => {
      if (!selectedIssue.value) return [];

      switch (selectedIssue.value.type) {
        case 'date_format':
          return [
            {
              description: '转换为标准日期格式 (YYYY-MM-DD)',
              preview: formatDate(selectedIssue.value.value)
            }
          ];
        case 'number_format':
          return [
            {
              description: '转换为数字格式',
              preview: parseFloat(selectedIssue.value.value).toFixed(2)
            }
          ];
        case 'missing_value':
          return [
            {
              description: '使用默认值',
              preview: '0'
            },
            {
              description: '使用最近一次的有效值',
              preview: '(使用历史数据)'
            }
          ];
        default:
          return [];
      }
    });

    // 处理错误修复
    const handleErrorFix = (error) => {
      selectedIssue.value = error;
      fixDialogType.value = 'error';
      selectedFix.value = null;
      fixDialogVisible.value = true;
    };

    // 处理警告修复
    const handleWarningFix = (warning) => {
      selectedIssue.value = warning;
      fixDialogType.value = 'warning';
      selectedFix.value = null;
      fixDialogVisible.value = true;
    };

    // 处理警告忽略
    const handleWarningIgnore = (warning) => {
      emit('warning-ignored', warning);
    };

    // 应用修复
    const applyFix = () => {
      if (selectedFix.value === null || !selectedIssue.value) return;

      emit('fix-applied', {
        issue: selectedIssue.value,
        fix: fixSuggestions.value[selectedFix.value]
      });
      fixDialogVisible.value = false;
    };

    // 继续导入
    const handleProceed = () => {
      emit('proceed');
    };

    // 取消导入
    const handleCancel = () => {
      emit('cancel');
    };

    // 格式化日期
    const formatDate = (dateStr) => {
      try {
        const date = new Date(dateStr);
        return date.toISOString().split('T')[0];
      } catch {
        return dateStr;
      }
    };

    return {
      activeTab,
      validationStatus,
      canProceed,
      fixDialogVisible,
      fixDialogTitle,
      selectedIssue,
      selectedFix,
      fixSuggestions,
      handleErrorFix,
      handleWarningFix,
      handleWarningIgnore,
      handleProceed,
      handleCancel,
      applyFix
    };
  }
};
&lt;/script>

&lt;style scoped>
.data-validation-feedback {
  margin: 20px 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.validation-summary {
  margin-bottom: 20px;
}

.error-count {
  color: #F56C6C;
  font-weight: bold;
}

.warning-count {
  color: #E6A23C;
  font-weight: bold;
}

.validation-details {
  margin-top: 20px;
}

.validation-actions {
  margin-top: 20px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.fix-suggestions {
  .issue-description {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #E6A23C;
    margin-bottom: 20px;
  }

  h4 {
    margin: 15px 0 10px;
    color: #303133;
  }
}

.fix-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fix-preview {
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
&lt;/style>