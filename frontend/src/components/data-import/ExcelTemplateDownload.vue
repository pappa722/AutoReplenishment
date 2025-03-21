&lt;template>
  &lt;div class="excel-template-download">
    &lt;el-card>
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>Excel模板下载&lt;/span>
          &lt;el-tooltip
            content="请使用标准模板导入数据，确保数据格式正确"
            placement="top"
          >
            &lt;el-icon>&lt;QuestionFilled />&lt;/el-icon>
          &lt;/el-tooltip>
        &lt;/div>
      &lt;/template>

      &lt;div class="template-list">
        &lt;el-row :gutter="20">
          &lt;el-col :span="8" v-for="template in templates" :key="template.id">
            &lt;div class="template-item">
              &lt;el-card shadow="hover">
                &lt;div class="template-icon">
                  &lt;el-icon :size="40" :color="template.iconColor">
                    &lt;component :is="template.icon" />
                  &lt;/el-icon>
                &lt;/div>
                &lt;h3>{{ template.name }}&lt;/h3>
                &lt;p>{{ template.description }}&lt;/p>
                &lt;div class="template-actions">
                  &lt;el-button
                    type="primary"
                    @click="downloadTemplate(template.id)"
                    :loading="downloading === template.id"
                  >
                    下载模板
                  &lt;/el-button>
                  &lt;el-button
                    type="info"
                    plain
                    @click="showTemplateGuide(template)"
                  >
                    使用说明
                  &lt;/el-button>
                &lt;/div>
              &lt;/el-card>
            &lt;/div>
          &lt;/el-col>
        &lt;/el-row>
      &lt;/div>
    &lt;/el-card>

    &lt;!-- 模板使用说明对话框 -->
    &lt;el-dialog
      v-model="guideDialogVisible"
      :title="selectedTemplate ? selectedTemplate.name + '使用说明' : '使用说明'"
      width="50%"
    >
      &lt;div v-if="selectedTemplate" class="template-guide">
        &lt;h4>模板说明&lt;/h4>
        &lt;p>{{ selectedTemplate.description }}&lt;/p>

        &lt;h4>字段说明&lt;/h4>
        &lt;el-table :data="selectedTemplate.fields" border style="width: 100%">
          &lt;el-table-column prop="name" label="字段名称" width="180">
          &lt;/el-table-column>
          &lt;el-table-column prop="type" label="数据类型" width="120">
          &lt;/el-table-column>
          &lt;el-table-column prop="required" label="是否必填" width="100">
            &lt;template #default="scope">
              &lt;el-tag :type="scope.row.required ? 'danger' : 'info'">
                {{ scope.row.required ? '是' : '否' }}
              &lt;/el-tag>
            &lt;/template>
          &lt;/el-table-column>
          &lt;el-table-column prop="description" label="说明">
          &lt;/el-table-column>
        &lt;/el-table>

        &lt;h4>注意事项&lt;/h4>
        &lt;ul>
          &lt;li v-for="(note, index) in selectedTemplate.notes" :key="index">
            {{ note }}
          &lt;/li>
        &lt;/ul>
      &lt;/div>
    &lt;/el-dialog>
  &lt;/div>
&lt;/template>

&lt;script>
import { ref } from 'vue';
import { useStore } from 'vuex';
import { Document, Goods, ShoppingCart } from '@element-plus/icons-vue';

export default {
  name: 'ExcelTemplateDownload',
  setup() {
    const store = useStore();
    const downloading = ref(null);
    const guideDialogVisible = ref(false);
    const selectedTemplate = ref(null);

    // 模板配置
    const templates = [
      {
        id: 'sales',
        name: '销售数据模板',
        description: '用于导入商品销售记录数据',
        icon: 'ShoppingCart',
        iconColor: '#409EFF',
        fields: [
          { name: '日期', type: '日期', required: true, description: '销售日期 (YYYY-MM-DD)' },
          { name: '商品编码', type: '文本', required: true, description: '商品唯一标识符' },
          { name: '销售数量', type: '数字', required: true, description: '销售数量（正整数）' },
          { name: '销售金额', type: '数字', required: true, description: '销售金额（元）' },
          { name: '折扣金额', type: '数字', required: false, description: '折扣金额（元）' }
        ],
        notes: [
          '日期格式必须为YYYY-MM-DD，例如：2024-03-21',
          '商品编码必须与系统中已有商品编码一致',
          '销售数量必须为正整数',
          '金额支持两位小数'
        ]
      },
      {
        id: 'inventory',
        name: '库存数据模板',
        description: '用于导入商品库存盘点数据',
        icon: 'Goods',
        iconColor: '#67C23A',
        fields: [
          { name: '盘点日期', type: '日期', required: true, description: '盘点日期 (YYYY-MM-DD)' },
          { name: '商品编码', type: '文本', required: true, description: '商品唯一标识符' },
          { name: '实际库存', type: '数字', required: true, description: '实际库存数量' },
          { name: '备注', type: '文本', required: false, description: '盘点备注信息' }
        ],
        notes: [
          '盘点日期格式必须为YYYY-MM-DD',
          '商品编码必须与系统中已有商品编码一致',
          '实际库存必须为非负整数',
          '建议每月至少进行一次全面盘点'
        ]
      },
      {
        id: 'products',
        name: '商品信息模板',
        description: '用于批量导入商品基础信息',
        icon: 'Document',
        iconColor: '#E6A23C',
        fields: [
          { name: '商品编码', type: '文本', required: true, description: '商品唯一标识符' },
          { name: '商品名称', type: '文本', required: true, description: '商品名称' },
          { name: '分类', type: '文本', required: true, description: '商品分类' },
          { name: '单位', type: '文本', required: true, description: '计量单位' },
          { name: '采购价', type: '数字', required: true, description: '采购价格（元）' },
          { name: '销售价', type: '数字', required: true, description: '销售价格（元）' },
          { name: '安全库存', type: '数字', required: true, description: '安全库存数量' }
        ],
        notes: [
          '商品编码必须唯一，建议使用字母和数字的组合',
          '商品分类必须与系统预设分类一致',
          '价格支持两位小数',
          '安全库存必须为正整数'
        ]
      }
    ];

    // 下载模板
    const downloadTemplate = async (templateId) => {
      downloading.value = templateId;
      try {
        const response = await store.dispatch('dataImport/downloadTemplate', { templateId });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${templateId}_template.xlsx`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('模板下载失败:', error);
      } finally {
        downloading.value = null;
      }
    };

    // 显示模板使用说明
    const showTemplateGuide = (template) => {
      selectedTemplate.value = template;
      guideDialogVisible.value = true;
    };

    return {
      templates,
      downloading,
      guideDialogVisible,
      selectedTemplate,
      downloadTemplate,
      showTemplateGuide
    };
  }
};
&lt;/script>

&lt;style scoped>
.excel-template-download {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-list {
  margin-top: 20px;
}

.template-item {
  margin-bottom: 20px;
}

.template-icon {
  text-align: center;
  margin-bottom: 15px;
}

.template-item h3 {
  margin: 0 0 10px 0;
  text-align: center;
}

.template-item p {
  margin: 0 0 15px 0;
  color: #666;
  text-align: center;
}

.template-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.template-guide {
  h4 {
    margin: 20px 0 10px;
    color: #303133;
  }

  ul {
    padding-left: 20px;
    margin: 10px 0;
    color: #666;
  }

  li {
    margin-bottom: 5px;
  }
}
&lt;/style>