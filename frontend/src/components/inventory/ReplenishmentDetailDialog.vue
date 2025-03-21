&lt;template>
  &lt;el-dialog
    v-model="dialogVisible"
    title="补货建议详情"
    width="800px"
    destroy-on-close
  >
    &lt;el-descriptions
      v-if="details"
      :column="2"
      border
    >
      &lt;el-descriptions-item label="商品编码">{{ details.productCode }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="商品名称">{{ details.productName }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="当前库存">{{ details.currentStock }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="安全库存">{{ details.safetyStock }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="建议补货量">{{ details.suggestedQuantity }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="预计销量">{{ details.forecastSales }}&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="补货优先级">
        &lt;el-tag :type="getPriorityType(details.priority)">{{ details.priority }}&lt;/el-tag>
      &lt;/el-descriptions-item>
      &lt;el-descriptions-item label="供应商提前期">{{ details.leadTime }}天&lt;/el-descriptions-item>
      &lt;el-descriptions-item label="建议原因" :span="2">{{ details.reason }}&lt;/el-descriptions-item>
    &lt;/el-descriptions>

    &lt;div class="charts-container" v-if="details">
      &lt;div class="chart">
        &lt;h4>历史销量趋势&lt;/h4>
        &lt;div ref="salesTrendChart" style="height: 300px">&lt;/div>
      &lt;/div>
      
      &lt;div class="chart">
        &lt;h4>库存水平分析&lt;/h4>
        &lt;div ref="stockLevelChart" style="height: 300px">&lt;/div>
      &lt;/div>
    &lt;/div>

    &lt;template #footer>
      &lt;span class="dialog-footer">
        &lt;el-button @click="dialogVisible = false">取消&lt;/el-button>
        &lt;el-button type="primary" @click="handleConfirm">
          确认补货
        &lt;/el-button>
      &lt;/template>
  &lt;/el-dialog>
&lt;/template>

&lt;script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useReplenishmentStore } from '@/store/modules/replenishment'
import * as echarts from 'echarts'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  productId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible', 'confirmed'])

const replenishmentStore = useReplenishmentStore()
const dialogVisible = ref(props.visible)
const details = ref(null)
const salesTrendChart = ref(null)
const stockLevelChart = ref(null)

// 监听visible属性变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
})

// 监听dialog可见性变化
watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
  if (newVal && props.productId) {
    loadDetails()
  }
})

// 加载详情数据
const loadDetails = async () => {
  try {
    details.value = await replenishmentStore.fetchAdviceDetails(props.productId)
    nextTick(() => {
      initCharts()
    })
  } catch (error) {
    ElMessage.error('加载详情失败')
  }
}

// 初始化图表
const initCharts = () => {
  // 销量趋势图
  const salesChart = echarts.init(salesTrendChart.value)
  salesChart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: details.value.salesTrend.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: details.value.salesTrend.map(item => item.quantity),
      type: 'line',
      smooth: true
    }]
  })

  // 库存水平分析图
  const stockChart = echarts.init(stockLevelChart.value)
  stockChart.setOption({
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['实际库存', '安全库存']
    },
    xAxis: {
      type: 'category',
      data: details.value.stockLevel.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '实际库存',
        type: 'line',
        data: details.value.stockLevel.map(item => item.actual)
      },
      {
        name: '安全库存',
        type: 'line',
        data: details.value.stockLevel.map(item => item.safety),
        lineStyle: {
          type: 'dashed'
        }
      }
    ]
  })
}

// 确认补货
const handleConfirm = async () => {
  try {
    await replenishmentStore.confirmReplenishment({
      productId: props.productId,
      quantity: details.value.suggestedQuantity
    })
    ElMessage.success('补货确认成功')
    dialogVisible.value = false
    emit('confirmed')
  } catch (error) {
    ElMessage.error('补货确认失败')
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

onMounted(() => {
  if (props.visible && props.productId) {
    loadDetails()
  }
})
&lt;/script>

&lt;style scoped>
.charts-container {
  margin-top: 20px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 20px;
}

.chart h4 {
  margin: 0 0 10px 0;
  color: #606266;
}
&lt;/style>