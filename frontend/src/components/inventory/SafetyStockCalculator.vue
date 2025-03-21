# frontend/src/components/inventory/SafetyStockCalculator.vue
<template>
  <div class="safety-stock-calculator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>动态安全库存计算</span>
          <div class="header-actions">
            <el-select v-model="categoryFilter" placeholder="商品分类" clearable size="small" style="width: 150px; margin-right: 10px;">
              <el-option
                v-for="category in categories"
                :key="category.value"
                :label="category.label"
                :value="category.value"
              />
            </el-select>
            <el-button-group>
              <el-button size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button size="small" @click="exportData">
                <el-icon><Download /></el-icon>
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>

      <!-- 参数配置区域 -->
      <div class="parameter-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="section-header">
                  <span>全局参数配置</span>
                  <el-tooltip
                    effect="dark"
                    content="设置安全库存计算的全局参数"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <el-form
                :model="globalParams"
                label-position="top"
                class="parameter-form"
              >
                <el-form-item label="服务水平">
                  <el-slider
                    v-model="globalParams.serviceLevel"
                    :min="80"
                    :max="99.99"
                    :step="0.01"
                    :format-tooltip="(val) => `${val}%`"
                  />
                  <div class="param-description">
                    设置目标服务水平，影响安全系数z值的计算
                  </div>
                </el-form-item>
                <el-form-item label="提前期（天）">
                  <el-input-number
                    v-model="globalParams.leadTime"
                    :min="1"
                    :max="90"
                    controls-position="right"
                  />
                  <div class="param-description">
                    从下单到收货的平均提前期
                  </div>
                </el-form-item>
                <el-form-item label="需求预测周期（天）">
                  <el-input-number
                    v-model="globalParams.forecastPeriod"
                    :min="7"
                    :max="90"
                    :step="7"
                    controls-position="right"
                  />
                  <div class="param-description">
                    需求预测的时间跨度
                  </div>
                </el-form-item>
                <el-form-item label="波动性评估方法">
                  <el-select v-model="globalParams.variabilityMethod" style="width: 100%">
                    <el-option label="标准差" value="std" />
                    <el-option label="平均绝对偏差" value="mad" />
                    <el-option label="变异系数" value="cv" />
                  </el-select>
                  <div class="param-description">
                    选择评估需求波动性的统计方法
                  </div>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header>
                <div class="section-header">
                  <span>分类参数配置</span>
                  <el-tooltip
                    effect="dark"
                    content="根据商品分类设置不同的安全库存参数"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <div class="category-params">
                <el-tabs v-model="activeCategory">
                  <el-tab-pane
                    v-for="category in categories"
                    :key="category.value"
                    :label="category.label"
                    :name="category.value"
                  >
                    <el-form
                      :model="categoryParams[category.value]"
                      label-position="top"
                      class="parameter-form"
                    >
                      <el-form-item label="服务水平调整">
                        <el-slider
                          v-model="categoryParams[category.value].serviceLevelAdjustment"
                          :min="-10"
                          :max="10"
                          :step="0.1"
                          :format-tooltip="(val) => (val >= 0 ? `+${val}%` : `${val}%`)"
                        />
                      </el-form-item>
                      <el-form-item label="提前期调整（天）">
                        <el-slider
                          v-model="categoryParams[category.value].leadTimeAdjustment"
                          :min="-5"
                          :max="5"
                          :step="1"
                          :format-tooltip="(val) => (val >= 0 ? `+${val}天` : `${val}天`)"
                        />
                      </el-form-item>
                      <el-form-item label="安全系数">
                        <el-input-number
                          v-model="categoryParams[category.value].safetyFactor"
                          :min="0.5"
                          :max="3"
                          :step="0.1"
                          :precision="2"
                          controls-position="right"
                        />
                      </el-form-item>
                      <el-form-item label="季节性调整">
                        <el-switch
                          v-model="categoryParams[category.value].seasonalityEnabled"
                          active-text="启用"
                          inactive-text="禁用"
                        />
                      </el-form-item>
                    </el-form>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 计算按钮 -->
      <div class="action-section">
        <el-button type="primary" :loading="calculating" @click="calculateSafetyStock">
          {{ calculating ? '计算中...' : '计算安全库存' }}
        </el-button>
        <el-button @click="resetParams">重置参数</el-button>
      </div>

      <!-- 计算结果展示 -->
      <div v-if="calculationResults.length > 0" class="results-section">
        <!-- 结果概览 -->
        <el-row :gutter="20" class="summary-cards">
          <el-col :span="6" v-for="metric in resultMetrics" :key="metric.label">
            <el-card shadow="hover" :body-style="{ padding: '15px' }">
              <div class="metric-item">
                <div class="metric-value" :class="getMetricClass(metric)">
                  {{ formatMetricValue(metric) }}
                  <span class="metric-unit">{{ metric.unit }}</span>
                </div>
                <div class="metric-label">{{ metric.label }}</div>
                <div class="metric-change" :class="metric.trend">
                  {{ metric.change }}%
                  <span>较上次计算</span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 安全库存分布图 -->
        <el-row :gutter="20" class="chart-section">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="chart-header">
                  <span>安全库存分布</span>
                  <el-tooltip
                    effect="dark"
                    content="展示不同商品类别的安全库存水平分布"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <div class="distribution-chart" ref="distributionChartRef"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="chart-header">
                  <span>需求波动性分析</span>
                  <el-tooltip
                    effect="dark"
                    content="展示各类商品的需求波动情况"
                    placement="top"
                  >
                    <el-icon><QuestionFilled /></el-icon>
                  </el-tooltip>
                </div>
              </template>
              <div class="variability-chart" ref="variabilityChartRef"></div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 详细结果表格 -->
      <el-card v-if="calculationResults.length > 0" class="table-card">
          <template #header>
            <div class="table-header">
              <span>计算结果</span>
              <div class="table-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索商品"
                  prefix-icon="Search"
                  clearable
                  size="small"
                  style="width: 200px; margin-right: 10px;"
                />
                <el-select v-model="stockLevelFilter" placeholder="库存水平" clearable size="small" style="width: 120px; margin-right: 10px;">
                  <el-option label="偏低" value="偏低" />
                  <el-option label="适中" value="适中" />
                  <el-option label="偏高" value="偏高" />
                </el-select>
                <el-button 
                  type="primary" 
                  size="small" 
                  :loading="calculating"
                  @click="calculateSafetyStock"
                >
                  计算安全库存
                </el-button>
                <el-button 
                  type="success" 
                  size="small" 
                  :disabled="multipleSelection.length === 0"
                  @click="batchApplyRecommendations"
                >
                  批量应用
                </el-button>
                <el-button 
                  type="warning" 
                  size="small" 
                  @click="autoUpdateAllSafetyStocks"
                >
                  自动更新全部
                </el-button>
              </div>
            </div>
          </template>
                <el-option label="适中" value="medium" />
                <el-option label="偏低" value="low" />
              </el-select>
            </div>
          </div>
        </template>

        <el-table
          :data="filteredResults"
          style="width: 100%"
          :max-height="400"
          v-loading="loading"
        >
          <el-table-column prop="product_code" label="商品编码" width="120" sortable />
          <el-table-column prop="product_name" label="商品名称" width="150" sortable />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="avg_demand" label="平均需求" width="100" sortable>
            <template #default="{ row }">
              {{ row.avg_demand.toFixed(1) }}
            </template>
          </el-table-column>
          <el-table-column prop="demand_std" label="需求标准差" width="120" sortable>
            <template #default="{ row }">
              {{ row.demand_std.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="lead_time" label="提前期" width="100">
            <template #default="{ row }">
              {{ row.lead_time }}天
            </template>
          </el-table-column>
          <el-table-column prop="service_level" label="服务水平" width="100">
            <template #default="{ row }">
              {{ row.service_level }}%
            </template>
          </el-table-column>
          <el-table-column prop="safety_stock" label="安全库存" width="100" sortable>
            <template #default="{ row }">
              <span :class="getStockLevelClass(row)">
                {{ row.safety_stock }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="reorder_point" label="再订货点" width="100" sortable />
          <el-table-column prop="stock_level" label="库存水平" width="100">
            <template #default="{ row }">
              <el-tag :type="getStockLevelType(row.stock_level)">
                {{ row.stock_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="suggestion" label="建议" min-width="150" />
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalItems"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </el-card>

    <!-- 计算详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="计算详情"
      width="70%"
    >
      <div v-if="selectedProduct" class="calculation-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="商品编码">{{ selectedProduct.product_code }}</el-descriptions-item>
          <el-descriptions-item label="商品名称">{{ selectedProduct.product_name }}</el-descriptions-item>
          <el-descriptions-item label="商品分类">{{ selectedProduct.category }}</el-descriptions-item>
          <el-descriptions-item label="服务水平">{{ selectedProduct.service_level }}%</el-descriptions-item>
          <el-descriptions-item label="平均需求">{{ selectedProduct.avg_demand }}</el-descriptions-item>
          <el-descriptions-item label="需求标准差">{{ selectedProduct.demand_std }}</el-descriptions-item>
          <el-descriptions-item label="提前期">{{ selectedProduct.lead_time }}天</el-descriptions-item>
          <el-descriptions-item label="安全系数">{{ selectedProduct.safety_factor }}</el-descriptions-item>
        </el-descriptions>

        <div class="calculation-steps">
          <h4>计算步骤</h4>
          <el-timeline>
            <el-timeline-item
              v-for="(step, index) in calculationSteps"
              :key="index"
              :type="step.type"
            >
              <h5>{{ step.title }}</h5>
              <p>{{ step.description }}</p>
              <div v-if="step.formula" class="step-formula">
                计算公式：{{ step.formula }}
              </div>
              <div v-if="step.result" class="step-result">
                计算结果：{{ step.result }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <div class="historical-chart">
          <div ref="historyChartRef" style="height: 300px;"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Download, QuestionFilled } from '@element-plus/icons-vue';
import axios from 'axios';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';

export default {
  name: 'SafetyStockCalculator',
  components: {
    Refresh,
    Download,
    QuestionFilled
  },
  setup() {
    // 状态定义
    const loading = ref(false);
    const calculating = ref(false);
    const categoryFilter = ref('');
    const activeCategory = ref('');
    const searchQuery = ref('');
    const stockLevelFilter = ref('');
    const currentPage = ref(1);
    const pageSize = ref(20);
    const totalItems = ref(0);
    const detailDialogVisible = ref(false);
    const selectedProduct = ref(null);
    const distributionChartRef = ref(null);
    const variabilityChartRef = ref(null);
    const historyChartRef = ref(null);

    // 计算结果
    const calculationResults = ref([]);

    // 结果概览指标
    const resultMetrics = ref([
      {
        label: '平均安全库存',
        value: 150,
        unit: '件',
        trend: 'up',
        change: 5.3,
        type: 'count'
      },
      {
        label: '平均服务水平',
        value: 96,
        unit: '%',
        trend: 'up',
        change: 1.2,
        type: 'percentage'
      },
      {
        label: '库存周转次数',
        value: 12.5,
        unit: '次/年',
        trend: 'down',
        change: -2.1,
        type: 'decimal'
      },
      {
        label: '库存金额',
        value: 285000,
        unit: '元',
        trend: 'up',
        change: 3.8,
        type: 'currency'
      }
    ]);

    // 计算步骤
    const calculationSteps = [
      {
        title: '步骤1：确定服务水平',
        description: '根据商品类别和重要性，结合全局服务水平进行调整',
        type: 'primary',
        formula: '实际服务水平 = 基础服务水平 + 类别调整',
        result: '95% + 2% = 97%'
      },
      {
        title: '步骤2：计算安全系数',
        description: '基于服务水平查找标准正态分布表得到安全系数',
        type: 'success',
        formula: 'Z(0.97) = 1.88',
        result: '安全系数 = 1.88'
      },
      {
        title: '步骤3：计算需求标准差',
        description: '分析历史数据计算日需求量的标准差',
        type: 'warning',
        formula: 'σ = sqrt(Σ(x-μ)²/n)',
        result: '日需求标准差 = 45件'
      },
      {
        title: '步骤4：计算安全库存',
        description: '综合考虑安全系数、需求波动和提前期',
        type: 'danger',
        formula: 'SS = Z * σ * sqrt(LT)',
        result: '安全库存 = 180件'
      }
    ]);

    // 从后端获取商品分类
    const categories = ref([]);
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/products/categories');
        categories.value = response.data.map(category => ({
          value: category.code,
          label: category.name
        }));
      } catch (error) {
        ElMessage.error('获取商品分类失败');
        console.error('Error fetching categories:', error);
      }
    };

    // 全局参数
    const globalParams = reactive({
      serviceLevel: 95,
      leadTime: 7,
      forecastPeriod: 28,
      variabilityMethod: 'std'
    });

    // 分类参数
    const categoryParams = reactive({
      food: {
        serviceLevelAdjustment: 2,
        leadTimeAdjustment: 1,
        safetyFactor: 1.2,
        seasonalityEnabled: true
      },
      drink: {
        serviceLevelAdjustment: 0,
        leadTimeAdjustment: 0,
        safetyFactor: 1.0,
        seasonalityEnabled: true
      },
      daily: {
        serviceLevelAdjustment: -2,
        leadTimeAdjustment: -1,
        safetyFactor: 0.8,
        seasonalityEnabled: false
      }
    });

    // 计算属性
    const filteredResults = computed(() => {
      let results = [...calculationResults.value];
      
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase();
        results = results.filter(item => 
          item.product_code.toLowerCase().includes(query) ||
          item.product_name.toLowerCase().includes(query)
        );
      }

      if (categoryFilter.value) {
        results = results.filter(item => 
          item.category === categoryFilter.value
        );
      }

      if (stockLevelFilter.value) {
        results = results.filter(item => 
          item.stock_level === stockLevelFilter.value
        );
      }

      totalItems.value = results.length;
      
      // 分页处理
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      return results.slice(start, end);
    });

    const effectiveServiceLevel = computed(() => {
      if (!activeCategory.value) return globalParams.serviceLevel;
      return globalParams.serviceLevel + 
        categoryParams[activeCategory.value].serviceLevelAdjustment;
    });

    const effectiveLeadTime = computed(() => {
      if (!activeCategory.value) return globalParams.leadTime;
      return globalParams.leadTime + 
        categoryParams[activeCategory.value].leadTimeAdjustment;
    });
    
    // API调用方法
    const loadSafetyStockData = async () => {
      loading.value = true;
      try {
        const response = await axios.get('/api/safety-stock/batch-calculate', {
          params: {
            skip: (currentPage.value - 1) * pageSize.value,
            limit: pageSize.value,
            category: categoryFilter.value || undefined
          }
        });
        
        calculationResults.value = response.data.items.map(item => ({
          product_id: item.productId,
          product_code: item.productCode,
          product_name: item.productName,
          category: item.category || '未分类',
          avg_demand: item.avgDemand,
          demand_std: item.demandStd,
          lead_time: item.leadTime,
          service_level: item.serviceLevel * 100,
          safety_stock: item.suggestedSafetyStock,
          current_safety_stock: item.currentSafetyStock,
          reorder_point: item.reorderPoint,
          stock_level: getStockLevelLabel(item.changePercentage),
          safety_factor: item.safetyFactor,
          confidence: item.confidenceLevel,
          suggestion: item.reason
        }));
        
        totalItems.value = response.data.total;
        
        // 更新结果指标
        updateResultMetrics(response.data.items);
        
        // 更新图表
        nextTick(() => {
          initDistributionChart();
          initVariabilityChart();
        });
      } catch (error) {
        ElMessage.error('加载安全库存数据失败');
        console.error('Error loading safety stock data:', error);
      } finally {
        loading.value = false;
      }
    };
    
    // 计算安全库存
    const calculateSafetyStock = async () => {
      calculating.value = true;
      try {
        // 准备参数
        const params = {
          serviceLevel: globalParams.serviceLevel / 100,
          historyPeriod: Math.ceil(globalParams.forecastPeriod / 30),
          leadTime: globalParams.leadTime,
          variabilityMethod: globalParams.variabilityMethod,
          considerSeasonality: true
        };
        
        // 如果有选择分类，添加分类特定参数
        if (activeCategory.value) {
          const catParams = categoryParams[activeCategory.value];
          params.serviceLevel += catParams.serviceLevelAdjustment / 100;
          params.leadTime += catParams.leadTimeAdjustment;
          params.safetyFactor = catParams.safetyFactor;
          params.considerSeasonality = catParams.seasonalityEnabled;
        }
        
        // 调用批量计算API
        const response = await axios.post('/api/safety-stock/batch-calculate', params, {
          params: {
            skip: (currentPage.value - 1) * pageSize.value,
            limit: pageSize.value,
            category: categoryFilter.value || undefined
          }
        });
        
        // 处理响应数据
        calculationResults.value = response.data.items.map(item => ({
          product_id: item.productId,
          product_code: item.productCode,
          product_name: item.productName,
          category: item.category || '未分类',
          avg_demand: item.avgDemand,
          demand_std: item.demandStd,
          lead_time: item.leadTime,
          service_level: item.serviceLevel * 100,
          safety_stock: item.suggestedSafetyStock,
          current_safety_stock: item.currentSafetyStock,
          reorder_point: item.reorderPoint,
          stock_level: getStockLevelLabel(item.changePercentage),
          safety_factor: item.safetyFactor,
          confidence: item.confidenceLevel,
          suggestion: item.reason
        }));
        
        totalItems.value = response.data.total;
        
        // 更新结果指标
        updateResultMetrics(response.data.items);
        
        // 更新图表
        nextTick(() => {
          initDistributionChart();
          initVariabilityChart();
        });
        
        ElMessage.success('安全库存计算完成');
      } catch (error) {
        ElMessage.error('计算安全库存失败');
        console.error('Error calculating safety stock:', error);
      } finally {
        calculating.value = false;
      }
    };
    
    // 更新结果指标
    const updateResultMetrics = (items) => {
      if (!items || items.length === 0) return;
      
      // 计算平均安全库存
      const avgSafetyStock = items.reduce((sum, item) => sum + item.suggestedSafetyStock, 0) / items.length;
      const prevAvgSafetyStock = items.reduce((sum, item) => sum + item.currentSafetyStock, 0) / items.length;
      const safetyStockChange = prevAvgSafetyStock ? ((avgSafetyStock - prevAvgSafetyStock) / prevAvgSafetyStock * 100) : 0;
      
      // 计算平均服务水平
      const avgServiceLevel = items.reduce((sum, item) => sum + item.serviceLevel, 0) / items.length * 100;
      
      // 估算库存周转次数和库存金额（示例计算）
      const turnoverRate = 12; // 示例值
      const inventoryValue = items.reduce((sum, item) => sum + item.suggestedSafetyStock * (item.unitCost || 100), 0);
      
      resultMetrics.value = [
        {
          label: '平均安全库存',
          value: Math.round(avgSafetyStock),
          unit: '件',
          trend: safetyStockChange > 0 ? 'up' : 'down',
          change: Math.abs(safetyStockChange).toFixed(1),
          type: 'count'
        },
        {
          label: '平均服务水平',
          value: avgServiceLevel.toFixed(1),
          unit: '%',
          trend: 'up',
          change: '0.0',
          type: 'percentage'
        },
        {
          label: '库存周转次数',
          value: turnoverRate,
          unit: '次/年',
          trend: 'neutral',
          change: '0.0',
          type: 'decimal'
        },
        {
          label: '库存金额',
          value: Math.round(inventoryValue),
          unit: '元',
          trend: safetyStockChange > 0 ? 'up' : 'down',
          change: Math.abs(safetyStockChange).toFixed(1),
          type: 'currency'
        }
      ];
    };
    
    // 获取库存水平标签
    const getStockLevelLabel = (changePercentage) => {
      if (changePercentage > 0.2) return '偏低';
      if (changePercentage < -0.2) return '偏高';
      return '适中';
    };

    // 图表初始化方法
    const initDistributionChart = () => {
      if (!distributionChartRef.value) return;
      
      const chart = echarts.init(distributionChartRef.value);
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '20',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: 35, name: '低库存' },
              { value: 45, name: '适中' },
              { value: 20, name: '高库存' }
            ]
          }
        ]
      };
      chart.setOption(option);
    };

    const initVariabilityChart = () => {
      if (!variabilityChartRef.value) return;
      
      const chart = echarts.init(variabilityChartRef.value);
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '变异系数'
        },
        yAxis: {
          type: 'category',
          data: ['食品', '饮料', '日用品']
        },
        series: [
          {
            type: 'bar',
            data: [0.35, 0.28, 0.42],
            itemStyle: {
              color: function(params) {
                const colors = ['#67c23a', '#409eff', '#e6a23c'];
                return colors[params.dataIndex];
              }
            },
            label: {
              show: true,
              position: 'right'
            }
          }
        ]
      };
      chart.setOption(option);
    };

    const initHistoryChart = () => {
      if (!historyChartRef.value || !selectedProduct.value) return;
      
      const chart = echarts.init(historyChartRef.value);
      const option = {
        title: {
          text: '历史安全库存变化',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['安全库存', '实际库存', '需求量'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['1月', '2月', '3月', '4月', '5月', '6月']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '安全库存',
            type: 'line',
            data: [120, 132, 101, 134, 90, 180],
            lineStyle: {
              color: '#409eff'
            }
          },
          {
            name: '实际库存',
            type: 'line',
            data: [220, 182, 191, 234, 290, 330],
            lineStyle: {
              color: '#67c23a'
            }
          },
          {
            name: '需求量',
            type: 'line',
            data: [150, 232, 201, 154, 190, 280],
            lineStyle: {
              color: '#e6a23c'
            }
          }
        ]
      };
      chart.setOption(option);
    };

    // 辅助方法
    const formatMetricValue = (metric) => {
      switch (metric.type) {
        case 'currency':
          return new Intl.NumberFormat('zh-CN', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
          }).format(metric.value);
        case 'percentage':
          return metric.value.toFixed(1);
        case 'decimal':
          return metric.value.toFixed(1);
        default:
          return metric.value;
      }
    };

    const getMetricClass = (metric) => {
      return metric.trend === 'up' ? 'up' : 'down';
    };

    const getStockLevelClass = (row) => {
      switch (row.stock_level) {
        case '偏高':
          return 'high-stock';
        case '偏低':
          return 'low-stock';
        default:
          return 'normal-stock';
      }
    };

    const getStockLevelType = (level) => {
      switch (level) {
        case '偏高':
          return 'warning';
        case '偏低':
          return 'danger';
        default:
          return 'success';
      }
    };

    // 方法定义
    const calculateSafetyStock = async () => {
      calculating.value = true;
      try {
        // TODO: 调用后端API计算安全库存
        await new Promise(resolve => setTimeout(resolve, 2000)); // 模拟API调用
        ElMessage.success('安全库存计算完成');
      } catch (error) {
        ElMessage.error('计算过程中出现错误');
      } finally {
        calculating.value = false;
      }
    };

    const resetParams = () => {
      // 重置全局参数
      globalParams.serviceLevel = 95;
      globalParams.leadTime = 7;
      globalParams.forecastPeriod = 28;
      globalParams.variabilityMethod = 'std';

      // 重置分类参数
      Object.keys(categoryParams).forEach(category => {
        categoryParams[category] = {
          serviceLevelAdjustment: 0,
          leadTimeAdjustment: 0,
          safetyFactor: 1.0,
          seasonalityEnabled: false
        };
      });

      ElMessage.success('参数已重置');
    };

    const refreshData = () => {
      loading.value = true;
      setTimeout(() => {
        loading.value = false;
        ElMessage.success('数据已更新');
      }, 800);
    };

    const exportData = () => {
      ElMessage.success('数据导出成功');
    };

    // 生命周期钩子
    onMounted(() => {
      nextTick(() => {
        initDistributionChart();
        initVariabilityChart();
      });
    });

    // 监听器
    watch([categoryFilter, stockLevelFilter, searchQuery], () => {
      currentPage.value = 1;
    });
    
    watch(currentPage, () => {
      loadSafetyStockData();
    });
    
    watch(pageSize, () => {
      currentPage.value = 1;
      loadSafetyStockData();
    });
    
    // 生命周期钩子
    onMounted(async () => {
      await Promise.all([
        fetchCategories(),
        loadSafetyStockData()
      ]);
      
      nextTick(() => {
        initDistributionChart();
        initVariabilityChart();
      });
    });

    // 分页方法
    const handleSizeChange = (val) => {
      pageSize.value = val;
      // 重新加载数据
    };

    const handleCurrentChange = (val) => {
      currentPage.value = val;
      // 重新加载数据
    };

    return {
      loading,
      calculating,
      categoryFilter,
      activeCategory,
      categories,
      globalParams,
      categoryParams,
      searchQuery,
      stockLevelFilter,
      currentPage,
      pageSize,
      totalItems,
      detailDialogVisible,
      selectedProduct,
      calculationResults,
      resultMetrics,
      calculationSteps,
      distributionChartRef,
      variabilityChartRef,
      historyChartRef,
      filteredResults,
      effectiveServiceLevel,
      effectiveLeadTime,
      formatMetricValue,
      getMetricClass,
      getStockLevelClass,
      getStockLevelType,
      calculateSafetyStock,
      resetParams,
      refreshData,
      exportData,
      handleSizeChange,
      handleCurrentChange
    };
  }
};
</script>

<style scoped>
.safety-stock-calculator {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.parameter-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.parameter-form {
  padding: 10px;
}

.param-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.category-params {
  min-height: 300px;
}

.action-section {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 20px 0;
}

.results-section {
  margin-top: 30px;
}

.summary-cards {
  margin-bottom: 30px;
}

.metric-item {
  text-align: center;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
}

.metric-unit {
  font-size: 14px;
  margin-left: 2px;
}

.metric-label {
  margin-top: 5px;
  color: #606266;
}

.metric-change {
  font-size: 12px;
  margin-top: 5px;
}

.metric-change.up {
  color: #67c23a;
}

.metric-change.down {
  color: #f56c6c;
}

.chart-section {
  margin-bottom: 30px;
}

.chart-card {
  height: 400px;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.distribution-chart,
.variability-chart {
  height: 320px;
  width: 100%;
}

.table-card {
  margin-top: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.calculation-details {
  padding: 10px;
}

.calculation-steps {
  margin-top: 30px;
}

.step-formula {
  color: #409eff;
  margin: 5px 0;
  font-family: monospace;
}

.step-result {
  color: #67c23a;
  margin-top: 5px;
}

.historical-chart {
  margin-top: 30px;
}

.high-stock {
  color: #e6a23c;
  font-weight: bold;
}

.normal-stock {
  color: #67c23a;
  font-weight: bold;
}

.low-stock {
  color: #f56c6c;
  font-weight: bold;
}

.metric-value.up {
  color: #67c23a;
}

.metric-value.down {
  color: #f56c6c;
}

:deep(.el-card__header) {
  padding: 15px 20px;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-slider) {
  margin-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}
</style>