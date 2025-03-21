import axios from 'axios';

const state = {
  // 导入会话信息
  session: {
    id: null,
    status: 'idle', // idle, validating, importing, completed, error
    step: 0, // 0: 选择模板, 1: 上传文件, 2: 验证数据, 3: 导入数据, 4: 完成
    progress: 0,
    currentOperation: '',
    errorMessage: ''
  },

  // 选择的模板信息
  selectedTemplate: null,

  // 上传的文件信息
  uploadedFile: null,
  uploadOptions: null,

  // 验证结果
  validationResult: {
    summary: {
      totalRecords: 0,
      validRecords: 0,
      errorRecords: 0,
      warningRecords: 0
    },
    errors: [],
    warnings: []
  },

  // 导入结果
  importResult: {
    totalRecords: 0,
    successRecords: 0,
    failedRecords: 0,
    completionStatus: 'success' // success, partial, failed
  },

  // 历史记录
  importHistory: []
};

const mutations = {
  // 更新会话信息
  SET_SESSION(state, session) {
    state.session = { ...state.session, ...session };
  },

  // 设置选中的模板
  SET_SELECTED_TEMPLATE(state, template) {
    state.selectedTemplate = template;
  },

  // 设置上传的文件
  SET_UPLOADED_FILE(state, { file, options }) {
    state.uploadedFile = file;
    state.uploadOptions = options;
  },

  // 更新验证结果
  SET_VALIDATION_RESULT(state, result) {
    state.validationResult = result;
  },

  // 更新导入结果
  SET_IMPORT_RESULT(state, result) {
    state.importResult = result;
  },

  // 添加导入历史
  ADD_IMPORT_HISTORY(state, record) {
    state.importHistory.unshift(record);
  },

  // 重置状态
  RESET_STATE(state) {
    state.session = {
      id: null,
      status: 'idle',
      step: 0,
      progress: 0,
      currentOperation: '',
      errorMessage: ''
    };
    state.selectedTemplate = null;
    state.uploadedFile = null;
    state.uploadOptions = null;
    state.validationResult = {
      summary: {
        totalRecords: 0,
        validRecords: 0,
        errorRecords: 0,
        warningRecords: 0
      },
      errors: [],
      warnings: []
    };
    state.importResult = {
      totalRecords: 0,
      successRecords: 0,
      failedRecords: 0,
      completionStatus: 'success'
    };
  }
};

const actions = {
  // 创建新的导入会话
  async createImportSession({ commit }) {
    try {
      const response = await axios.post('/api/data-import/sessions');
      commit('SET_SESSION', {
        id: response.data.sessionId,
        status: 'idle',
        step: 0
      });
      return response.data.sessionId;
    } catch (error) {
      throw new Error('创建导入会话失败: ' + error.message);
    }
  },

  // 下载模板文件
  async downloadTemplate({ commit }, { templateId }) {
    try {
      const response = await axios.get(`/api/data-import/templates/${templateId}`, {
        responseType: 'blob'
      });
      return response;
    } catch (error) {
      throw new Error('模板下载失败: ' + error.message);
    }
  },

  // 上传文件
  async uploadFile({ commit, state }, { file, options }) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('sessionId', state.session.id);
      formData.append('options', JSON.stringify(options));

      const response = await axios.post('/api/data-import/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      commit('SET_UPLOADED_FILE', { file, options });
      return response.data;
    } catch (error) {
      throw new Error('文件上传失败: ' + error.message);
    }
  },

  // 验证数据
  async validateData({ commit, state }) {
    try {
      commit('SET_SESSION', {
        status: 'validating',
        step: 2,
        progress: 0,
        currentOperation: '正在验证数据...'
      });

      const response = await axios.post(`/api/data-import/sessions/${state.session.id}/validate`);
      
      commit('SET_VALIDATION_RESULT', response.data);
      commit('SET_SESSION', {
        status: response.data.summary.errorRecords > 0 ? 'error' : 'idle',
        progress: 100
      });

      return response.data;
    } catch (error) {
      commit('SET_SESSION', {
        status: 'error',
        errorMessage: '数据验证失败: ' + error.message
      });
      throw error;
    }
  },

  // 应用修复建议
  async applyFix({ commit, state }, { issue, fix }) {
    try {
      const response = await axios.post(`/api/data-import/sessions/${state.session.id}/fixes`, {
        issue,
        fix
      });

      // 更新验证结果
      commit('SET_VALIDATION_RESULT', response.data);
      return response.data;
    } catch (error) {
      throw new Error('应用修复建议失败: ' + error.message);
    }
  },

  // 忽略警告
  async ignoreWarning({ commit, state }, warning) {
    try {
      const response = await axios.post(`/api/data-import/sessions/${state.session.id}/warnings/ignore`, {
        warning
      });

      // 更新验证结果
      commit('SET_VALIDATION_RESULT', response.data);
      return response.data;
    } catch (error) {
      throw new Error('忽略警告失败: ' + error.message);
    }
  },

  // 开始导入数据
  async startImport({ commit, state }) {
    try {
      commit('SET_SESSION', {
        status: 'importing',
        step: 3,
        progress: 0,
        currentOperation: '正在导入数据...'
      });

      const response = await axios.post(`/api/data-import/sessions/${state.session.id}/import`);
      
      commit('SET_IMPORT_RESULT', response.data);
      commit('SET_SESSION', {
        status: 'completed',
        step: 4,
        progress: 100,
        currentOperation: '导入完成'
      });

      // 添加到导入历史
      commit('ADD_IMPORT_HISTORY', {
        id: state.session.id,
        timestamp: new Date().toISOString(),
        template: state.selectedTemplate,
        result: response.data
      });

      return response.data;
    } catch (error) {
      commit('SET_SESSION', {
        status: 'error',
        errorMessage: '数据导入失败: ' + error.message
      });
      throw error;
    }
  },

  // 取消导入
  async cancelImport({ commit, state }) {
    try {
      await axios.delete(`/api/data-import/sessions/${state.session.id}`);
      commit('RESET_STATE');
    } catch (error) {
      throw new Error('取消导入失败: ' + error.message);
    }
  },

  // 重置导入状态
  resetImportState({ commit }) {
    commit('RESET_STATE');
  }
};

const getters = {
  // 当前导入进度
  importProgress: state => state.session.progress,

  // 是否可以继续下一步
  canProceed: state => {
    switch (state.session.step) {
      case 0: // 选择模板
        return state.selectedTemplate !== null;
      case 1: // 上传文件
        return state.uploadedFile !== null;
      case 2: // 验证数据
        return state.validationResult.summary.errorRecords === 0;
      case 3: // 导入数据
        return state.session.status !== 'importing';
      default:
        return false;
    }
  },

  // 验证是否通过
  isValidationPassed: state => {
    return state.validationResult.summary.errorRecords === 0;
  },

  // 导入是否成功
  isImportSuccessful: state => {
    return state.session.status === 'completed' &&
           state.importResult.completionStatus === 'success';
  }
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};