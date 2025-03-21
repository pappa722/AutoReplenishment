&lt;template>
  &lt;div class="import-progress-tracker">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>导入进度&lt;/span>
          &lt;el-tag :type="statusTag.type">{{ statusTag.text }}&lt;/el-tag>
        &lt;/div>
      &lt;/template>

      &lt;div class="progress-container">
        &lt;!-- 步骤指示器 -->
        &lt;el-steps :active="activeStep" finish-status="success" align-center>
          &lt;el-step title="文件上传" icon="UploadFilled" />
          &lt;el-step title="数据验证" icon="DocumentChecked" />
          &lt;el-step title="数据导入" icon="DataLine" />
          &lt;el-step title="完成" icon="CircleCheckFilled" />
        &lt;/el-steps>

        &lt;!-- 进度条 -->
        &lt;div class="progress-bar-container" v-if="showProgressBar">
          &lt;div class="progress-info">
            &lt;span>{{ progressText }}&lt;/span>
            &lt;span>{{ progressPercentage }}%&lt;/span>
          &lt;/div>
          &lt;el-progress
            :percentage="progressPercentage"
            :status="progressStatus"
            :stroke-width="20"
            :format="() => ''"
          />
        &lt;/div>

        &lt;!-- 导入统计 -->
        &lt;div class="import-stats" v-if="showStats">
          &lt;el-row :gutter="20">
            &lt;el-col :span="8">
              &lt;el-statistic title="总记录数" :value="stats.totalRecords">
                &lt;template #suffix>
                  &lt;span class="suffix">条&lt;/span>
                &lt;/template>
              &lt;/el-statistic>
            &lt;/el-col>
            &lt;el-col :span="8">
              &lt;el-statistic
                title="成功导入"
                :value="stats.successRecords"
                value-style="color: #67C23A"
              >
                &lt;template #suffix>
                  &lt;span class="suffix">条&lt;/span>
                &lt;/template>
              &lt;/el-statistic>
            &lt;/el-col>
            &lt;el-col :span="8">
              &lt;el-statistic
                title="失败记录"
                :value="stats.failedRecords"
                value-style="color: #F56C6C"
              >
                &lt;template #suffix>
                  &lt;span class="suffix">条&lt;/span>
                &lt;/template>
              &lt;/el-statistic>
            &lt;/el-col>
          &lt;/el-row>
        &lt;/div>

        &lt;!-- 当前操作详情 -->
        &lt;div class="current-operation" v-if="currentOperation">
          &lt;el-alert
            :title="currentOperation"
            type="info"
            :closable="false"
            center
            show-icon
          />
        &lt;/div>

        &lt;!-- 错误信息 -->
        &lt;div class="error-message" v-if="errorMessage">
          &lt;el-alert
            :title="errorMessage"
            type="error"
            :closable="false"
            show-icon
          />
        &lt;/div>

        &lt;!-- 完成信息 -->
        &lt;div class="completion-message" v-if="isCompleted">
          &lt;el-result
            :icon="completionStatus === 'success' ? 'success' : 'warning'"
            :title="completionTitle"
            :sub-title="completionSubtitle"
          >
            &lt;template #extra>
              &lt;el-button type="primary" @click="$emit('view-results')">
                查看导入结果
              &lt;/el-button>
              &lt;el-button @click="$emit('new-import')">新建导入&lt;/el-button>
            &lt;/template>
          &lt;/el-result>
        &lt;/div>
      &lt;/div>

      &lt;!-- 操作按钮 -->
      &lt;div class="action-buttons" v-if="showActionButtons">
        &lt;el-button
          type="primary"
          :disabled="!canProceed"
          @click="$emit('proceed')"
        >
          {{ proceedButtonText }}
        &lt;/el-button>
        &lt;el-button @click="$emit('cancel')">取消导入&lt;/el-button>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script>
import { computed } from 'vue';
import {
  UploadFilled,
  DocumentChecked,
  DataLine,
  CircleCheckFilled
} from '@element-plus/icons-vue';

export default {
  name: 'ImportProgressTracker',
  props: {
    // 当前步骤 (0: 上传, 1: 验证, 2: 导入, 3: 完成)
    step: {
      type: Number,
      required: true
    },
    // 导入状态 (idle, validating, importing, completed, error)
    status: {
      type: String,
      required: true
    },
    // 进度百分比 (0-100)
    progress: {
      type: Number,
      default: 0
    },
    // 导入统计数据
    stats: {
      type: Object,
      default: () => ({
        totalRecords: 0,
        successRecords: 0,
        failedRecords: 0
      })
    },
    // 当前操作描述
    currentOperation: {
      type: String,
      default: ''
    },
    // 错误信息
    errorMessage: {
      type: String,
      default: ''
    },
    // 完成状态 (success, partial, failed)
    completionStatus: {
      type: String,
      default: 'success'
    }
  },
  emits: ['proceed', 'cancel', 'view-results', 'new-import'],
  setup(props) {
    // 计算活动步骤
    const activeStep = computed(() => props.step);

    // 计算状态标签
    const statusTag = computed(() => {
      switch (props.status) {
        case 'idle':
          return { type: 'info', text: '准备中' };
        case 'validating':
          return { type: 'warning', text: '验证中' };
        case 'importing':
          return { type: 'primary', text: '导入中' };
        case 'completed':
          return { type: 'success', text: '已完成' };
        case 'error':
          return { type: 'danger', text: '出错' };
        default:
          return { type: 'info', text: '未知状态' };
      }
    });

    // 计算进度条状态
    const progressStatus = computed(() => {
      if (props.status === 'error') return 'exception';
      if (props.progress === 100) return 'success';
      return '';
    });

    // 计算进度文本
    const progressText = computed(() => {
      switch (props.status) {
        case 'validating':
          return '正在验证数据...';
        case 'importing':
          return '正在导入数据...';
        case 'completed':
          return '导入完成';
        case 'error':
          return '导入出错';
        default:
          return '';
      }
    });

    // 计算进度百分比
    const progressPercentage = computed(() => {
      return Math.min(Math.max(props.progress, 0), 100);
    });

    // 计算是否显示进度条
    const showProgressBar = computed(() => {
      return ['validating', 'importing'].includes(props.status);
    });

    // 计算是否显示统计数据
    const showStats = computed(() => {
      return props.status === 'completed' || 
             (props.status === 'importing' && props.progress > 0);
    });

    // 计算是否已完成
    const isCompleted = computed(() => {
      return props.status === 'completed' || props.status === 'error';
    });

    // 计算完成标题
    const completionTitle = computed(() => {
      if (props.status !== 'completed') return '';
      
      switch (props.completionStatus) {
        case 'success':
          return '导入成功';
        case 'partial':
          return '部分导入成功';
        case 'failed':
          return '导入失败';
        default:
          return '导入完成';
      }
    });

    // 计算完成副标题
    const completionSubtitle = computed(() => {
      if (props.status !== 'completed') return '';
      
      const { totalRecords, successRecords, failedRecords } = props.stats;
      
      switch (props.completionStatus) {
        case 'success':
          return `成功导入 ${totalRecords} 条记录`;
        case 'partial':
          return `共 ${totalRecords} 条记录，成功 ${successRecords} 条，失败 ${failedRecords} 条`;
        case 'failed':
          return '导入过程中出现错误，请检查数据格式后重试';
        default:
          return '';
      }
    });

    // 计算是否显示操作按钮
    const showActionButtons = computed(() => {
      return props.status !== 'completed' && props.status !== 'error';
    });

    // 计算是否可以继续
    const canProceed = computed(() => {
      return props.status !== 'importing' && props.status !== 'error';
    });

    // 计算继续按钮文本
    const proceedButtonText = computed(() => {
      switch (props.step) {
        case 0:
          return '开始验证';
        case 1:
          return '开始导入';
        default:
          return '继续';
      }
    });

    return {
      activeStep,
      statusTag,
      progressStatus,
      progressText,
      progressPercentage,
      showProgressBar,
      showStats,
      isCompleted,
      completionTitle,
      completionSubtitle,
      showActionButtons,
      canProceed,
      proceedButtonText
    };
  }
};
&lt;/script>

&lt;style scoped>
.import-progress-tracker {
  margin: 20px 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-container {
  padding: 20px 0;
}

.progress-bar-container {
  margin: 30px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  color: #606266;
}

.import-stats {
  margin: 30px 0;
}

.suffix {
  font-size: 14px;
  margin-left: 4px;
}

.current-operation {
  margin: 20px 0;
}

.error-message {
  margin: 20px 0;
}

.completion-message {
  margin: 30px 0;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
}
&lt;/style>