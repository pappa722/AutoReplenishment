&lt;template>
  &lt;div class="file-uploader">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>文件上传&lt;/span>
          &lt;el-tooltip
            content="支持Excel文件格式：.xlsx, .xls"
            placement="top"
          >
            &lt;el-icon>&lt;QuestionFilled />&lt;/el-icon>
          &lt;/el-tooltip>
        &lt;/div>
      &lt;/template>

      &lt;div class="upload-container">
        &lt;el-upload
          class="upload-area"
          drag
          :action="uploadAction"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :on-exceed="handleExceed"
          :before-upload="beforeUpload"
          :file-list="fileList"
          accept=".xlsx,.xls"
        >
          &lt;el-icon class="upload-icon">&lt;Upload />&lt;/el-icon>
          &lt;div class="upload-text">
            &lt;em>点击上传或拖拽文件到此区域&lt;/em>
            &lt;p class="upload-hint">支持Excel文件格式：.xlsx, .xls&lt;/p>
          &lt;/div>
        &lt;/el-upload>
      &lt;/div>

      &lt;div class="file-info" v-if="currentFile">
        &lt;el-descriptions title="文件信息" :column="1" border>
          &lt;el-descriptions-item label="文件名">
            {{ currentFile.name }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="文件大小">
            {{ formatFileSize(currentFile.size) }}
          &lt;/el-descriptions-item>
          &lt;el-descriptions-item label="上传时间">
            {{ formatDate(currentFile.lastModified) }}
          &lt;/el-descriptions-item>
        &lt;/el-descriptions>
      &lt;/div>

      &lt;div class="import-options" v-if="currentFile">
        &lt;el-divider>导入选项&lt;/el-divider>
        
        &lt;el-form :model="importOptions" label-position="top">
          &lt;el-form-item label="数据类型">
            &lt;el-select v-model="importOptions.dataType" placeholder="请选择数据类型">
              &lt;el-option
                v-for="option in dataTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            &lt;/el-select>
          &lt;/el-form-item>

          &lt;el-form-item label="导入模式">
            &lt;el-radio-group v-model="importOptions.importMode">
              &lt;el-radio label="append">追加数据&lt;/el-radio>
              &lt;el-radio label="update">更新已有数据&lt;/el-radio>
              &lt;el-radio label="replace">替换数据&lt;/el-radio>
            &lt;/el-radio-group>
          &lt;/el-form-item>

          &lt;el-form-item label="高级选项">
            &lt;el-checkbox v-model="importOptions.skipFirstRow">
              跳过首行（标题行）
            &lt;/el-checkbox>
            &lt;el-checkbox v-model="importOptions.validateOnly">
              仅验证数据（不导入）
            &lt;/el-checkbox>
          &lt;/el-form-item>
        &lt;/el-form>
      &lt;/div>

      &lt;div class="upload-actions" v-if="currentFile">
        &lt;el-button
          type="primary"
          @click="handleUpload"
          :loading="uploading"
        >
          开始上传
        &lt;/el-button>
        &lt;el-button @click="resetUpload">重置&lt;/el-button>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref, reactive, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Upload, QuestionFilled } from '@element-plus/icons-vue';

export default {
  name: 'FileUploader',
  props: {
    // API上传地址
    uploadUrl: {
      type: String,
      default: '/api/data-import/upload'
    }
  },
  emits: ['file-uploaded', 'upload-failed', 'reset'],
  setup(props, { emit }) {
    const fileList = ref([]);
    const currentFile = ref(null);
    const uploading = ref(false);
    
    // 导入选项
    const importOptions = reactive({
      dataType: 'sales', // 默认为销售数据
      importMode: 'append', // 默认为追加模式
      skipFirstRow: true, // 默认跳过首行
      validateOnly: false // 默认不仅验证
    });

    // 数据类型选项
    const dataTypeOptions = [
      { label: '销售数据', value: 'sales' },
      { label: '库存数据', value: 'inventory' },
      { label: '商品信息', value: 'products' }
    ];

    // 计算上传地址
    const uploadAction = computed(() => {
      return props.uploadUrl;
    });

    // 文件变更处理
    const handleFileChange = (file) => {
      if (file.status === 'ready') {
        currentFile.value = file.raw;
        fileList.value = [file];
      }
    };

    // 文件移除处理
    const handleFileRemove = () => {
      currentFile.value = null;
      fileList.value = [];
    };

    // 文件数量超出限制处理
    const handleExceed = () => {
      ElMessage.warning('只能上传一个文件，请先删除当前文件');
    };

    // 上传前验证
    const beforeUpload = (file) => {
      const isExcel = 
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
        file.type === 'application/vnd.ms-excel';
      
      if (!isExcel) {
        ElMessage.error('只能上传Excel文件!');
        return false;
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10;
      
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过10MB!');
        return false;
      }
      
      return true;
    };

    // 开始上传
    const handleUpload = async () => {
      if (!currentFile.value) {
        ElMessage.warning('请先选择要上传的文件');
        return;
      }

      uploading.value = true;
      
      try {
        // 创建表单数据
        const formData = new FormData();
        formData.append('file', currentFile.value);
        formData.append('dataType', importOptions.dataType);
        formData.append('importMode', importOptions.importMode);
        formData.append('skipFirstRow', importOptions.skipFirstRow);
        formData.append('validateOnly', importOptions.validateOnly);

        // 模拟上传过程
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 触发上传成功事件
        emit('file-uploaded', {
          file: currentFile.value,
          options: { ...importOptions },
          // 模拟返回的文件ID
          fileId: 'file_' + Date.now()
        });
      } catch (error) {
        console.error('上传失败:', error);
        emit('upload-failed', error);
        ElMessage.error('文件上传失败，请重试');
      } finally {
        uploading.value = false;
      }
    };

    // 重置上传
    const resetUpload = () => {
      currentFile.value = null;
      fileList.value = [];
      
      // 重置导入选项
      importOptions.dataType = 'sales';
      importOptions.importMode = 'append';
      importOptions.skipFirstRow = true;
      importOptions.validateOnly = false;
      
      emit('reset');
    };

    // 格式化文件大小
    const formatFileSize = (size) => {
      if (size < 1024) {
        return size + ' B';
      } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB';
      } else {
        return (size / (1024 * 1024)).toFixed(2) + ' MB';
      }
    };

    // 格式化日期
    const formatDate = (timestamp) => {
      const date = new Date(timestamp);
      return date.toLocaleString();
    };

    return {
      fileList,
      currentFile,
      uploading,
      importOptions,
      dataTypeOptions,
      uploadAction,
      handleFileChange,
      handleFileRemove,
      handleExceed,
      beforeUpload,
      handleUpload,
      resetUpload,
      formatFileSize,
      formatDate
    };
  }
};
&lt;/script>

&lt;style scoped>
.file-uploader {
  margin: 20px 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-container {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.upload-area {
  width: 100%;
}

.upload-icon {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}

.upload-text {
  color: #606266;
  font-size: 16px;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}

.file-info {
  margin: 20px 0;
}

.import-options {
  margin: 20px 0;
}

.upload-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}
&lt;/style>