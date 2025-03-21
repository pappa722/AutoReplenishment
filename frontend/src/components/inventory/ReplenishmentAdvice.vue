&lt;template>
  &lt;div class="replenishment-advice">
    &lt;el-card class="advice-card">
      &lt;template #header>
        &lt;div class="card-header">
          &lt;span>智能补货建议&lt;/span>
          &lt;el-button type="primary" @click="generateAdvice">生成建议&lt;/el-button>
        &lt;/div>
      &lt;/template>

      &lt;div class="advice-filters">
        &lt;el-form :inline="true" :model="filterForm">
          &lt;el-form-item label="商品类别">
            &lt;el-select v-model="filterForm.category" placeholder="选择商品类别">
              &lt;el-option
                v-for="item in store.categories"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            &lt;/el-select>
          &lt;/el-form-item>
          &lt;el-form-item label="补货优先级">
            &lt;el-select v-model="filterForm.priority" placeholder="选择优先级">
              &lt;el-option label="高" value="high" />
              &lt;el-option label="中" value="medium" />
              &lt;el-option label="低" value="low" />
            &lt;/el-select>
          &lt;/el-form-item>
        &lt;/el-form>
      &lt;/div>

      &lt;el-table
        v-loading="store.loading"
        :data="store.adviceList"
        style="width: 100%"
        border
      >
        &lt;el-table-column prop="productCode" label="商品编码" width="120" />
        &lt;el-table-column prop="productName" label="商品名称" width="180" />
        &lt;el-table-column prop="currentStock" label="当前库存" width="100" />
        &lt;el-table-column prop="suggestedQuantity" label="建议补货量" width="120" />
        &lt;el-table-column prop="priority" label="优先级" width="100">
          &lt;template #default="scope">
            &lt;el-tag :type="getPriorityType(scope.row.priority)">
              {{ scope.row.priority }}
            &lt;/el-tag>
          &lt;/template>
        &lt;/el-table-column>
        &lt;el-table-column prop="reason" label="建议原因" />
        &lt;el-table-column label="操作" width="150" fixed="right">
          &lt;template #default="scope">
            &lt;el-button
              type="primary"
              link
              @click="viewDetails(scope.row)"
            >
              详情
            &lt;/el-button>
            &lt;el-button
              type="success"
              link
              @click="confirmReplenishment(scope.row)"
            >
              确认补货
            &lt;/el-button>
          &lt;/template>
        &lt;/el-table-column>
      &lt;/el-table>

      &lt;div class="table-footer">
        &lt;el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="store.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
        &lt;el-button type="success" @click="exportAdvice">导出补货建议&lt;/el-button>
      &lt;/div>
    &lt;/el-card>
  &lt;/div>
&lt;/template>

&lt;script setup>
import { ref, reactive, onMounted } from 'vue'
import { useReplenishmentStore } from '@/store/modules/replenishment'
import { ElMessage, ElMessageBox } from 'element-plus'
import ReplenishmentDetailDialog from './ReplenishmentDetailDialog.vue'

const store = useReplenishmentStore()

// 过滤表单数据
const filterForm = reactive({
  category: '',
  priority: ''
})

// 分页相关数据
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 模拟商品类别数据
const categories = [
  { value: 'food', label: '食品' },
  { value: 'drink', label: '饮料' },
  { value: 'daily', label: '日用品' }
]

// 详情对话框控制
const detailDialogVisible = ref(false)
const currentProductId = ref('')

// 生成补货建议
const generateAdvice = async () => {
  try {
    await store.fetchAdviceList({
      page: currentPage.value,
      pageSize: pageSize.value,
      filters: filterForm
    })
  } catch (error) {
    ElMessage.error('获取补货建议失败')
  }
}

// 获取优先级标签类型
const getPriorityType = (priority) => {
  const types = {
    '高': 'danger',
    '中': 'warning',
    '低': 'info'
  }
  return types[priority] || 'info'
}

// 查看详情
const viewDetails = (row) => {
  currentProductId.value = row.id
  detailDialogVisible.value = true
}

// 确认补货
const confirmReplenishment = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认为商品 ${row.productName} 补货 ${row.suggestedQuantity} 个单位？`,
      '确认补货',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await store.confirmReplenishment({
      productId: row.id,
      quantity: row.suggestedQuantity
    })
    
    ElMessage.success('补货确认成功')
    generateAdvice() // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('补货确认失败')
    }
  }
}

// 导出补货建议
const exportAdvice = async () => {
  try {
    await store.exportAdvice(filterForm)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 处理补货确认后的回调
const handleReplenishmentConfirmed = () => {
  generateAdvice() // 刷新列表
}

// 初始化数据
onMounted(async () => {
  try {
    await store.fetchCategories()
    await generateAdvice()
  } catch (error) {
    ElMessage.error('初始化数据失败')
  }
})

// 处理分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  generateAdvice()
}

// 处理页码变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  generateAdvice()
}
&lt;/script>

&lt;!-- 补货详情对话框 -->
&lt;ReplenishmentDetailDialog
  v-model:visible="detailDialogVisible"
  :product-id="currentProductId"
  @confirmed="handleReplenishmentConfirmed"
/>

&lt;style scoped>
.replenishment-advice {
  padding: 20px;
}

.advice-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.advice-filters {
  margin-bottom: 20px;
}

.table-footer {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
&lt;/style>