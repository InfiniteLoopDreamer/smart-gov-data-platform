// 模拟数据（首页看板与各页面共用）

// 顶部统计卡
export const statCards = [
  { title: '今日办件量', value: '1286', unit: '件', icon: 'Document', color: '#2B5FD7', trend: '↑ 12.4% 较昨日', trendType: 'up' },
  { title: '完成率', value: '96.8', unit: '%', icon: 'CircleCheck', color: '#10B981', trend: '↑ 2.1% 较上周', trendType: 'up' },
  { title: '待办事项', value: '42', unit: '件', icon: 'Clock', color: '#F59E0B', trend: '↓ 8 件 较昨日', trendType: 'down' },
  { title: '本月累计', value: '38,520', unit: '件', icon: 'DataAnalysis', color: '#8B5CF6', trend: '↑ 6.8% 较上月', trendType: 'up' }
]

// 近 30 天办件趋势（确定性生成，保证每次一致）
export const trendData = (() => {
  const dates = []
  const values = []
  const base = new Date()
  for (let i = 29; i >= 0; i--) {
    const d = new Date(base)
    d.setDate(d.getDate() - i)
    dates.push(`${d.getMonth() + 1}/${d.getDate()}`)
    // 基线 + 双周期波动，模拟真实业务趋势
    const wave = Math.round(
      1000 + 300 * Math.sin((29 - i) / 3.5) + 120 * Math.sin((29 - i) / 1.3)
    )
    values.push(wave)
  }
  return { dates, values }
})()

// 各区域办件量
export const regionData = [
  { name: '城东区', value: 1580 },
  { name: '城西区', value: 1260 },
  { name: '城南区', value: 1420 },
  { name: '城北区', value: 980 },
  { name: '高新区', value: 1760 },
  { name: '经开区', value: 1120 },
  { name: '滨湖区', value: 860 },
  { name: '新城区', value: 690 }
]

// 最近办件记录
export const caseRecords = [
  { id: 'BJ2024060101', applicant: '张伟', region: '城东区', status: '已办结', time: '2024-06-01 09:12' },
  { id: 'BJ2024060102', applicant: '李娜', region: '高新区', status: '办理中', time: '2024-06-01 09:35' },
  { id: 'BJ2024060103', applicant: '王强', region: '城南区', status: '待审批', time: '2024-06-01 10:02' },
  { id: 'BJ2024060104', applicant: '刘洋', region: '经开区', status: '已办结', time: '2024-06-01 10:18' },
  { id: 'BJ2024060105', applicant: '陈静', region: '城西区', status: '已驳回', time: '2024-06-01 10:47' },
  { id: 'BJ2024060106', applicant: '赵磊', region: '滨湖区', status: '办理中', time: '2024-06-01 11:05' },
  { id: 'BJ2024060107', applicant: '孙敏', region: '新城区', status: '已办结', time: '2024-06-01 11:30' },
  { id: 'BJ2024060108', applicant: '周涛', region: '城北区', status: '待受理', time: '2024-06-01 11:52' }
]

// 用户管理（前端兜底数据，后端可用时以 /api/users 为准）
export const users = [
  { id: 1, name: '系统管理员', username: 'admin', role: '管理员', department: '信息中心', status: '启用', lastLogin: '2024-06-01 08:30' },
  { id: 2, name: '张伟', username: 'zhangwei', role: '普通用户', department: '办件中心', status: '启用', lastLogin: '2024-06-01 09:12' },
  { id: 3, name: '李娜', username: 'lina', role: '普通用户', department: '审批科', status: '启用', lastLogin: '2024-05-31 17:45' },
  { id: 4, name: '王强', username: 'wangqiang', role: '普通用户', department: '大数据中心', status: '启用', lastLogin: '2024-05-31 16:20' },
  { id: 5, name: '刘洋', username: 'liuyang', role: '普通用户', department: '外部单位', status: '停用', lastLogin: '2024-05-20 10:05' }
]

// 通知
export const notifications = [
  { id: 1, title: '有 3 件办件即将超时，请尽快处理', type: 'warning', time: '10 分钟前', read: false },
  { id: 2, title: '数据清洗任务已完成，共清洗 61 条', type: 'success', time: '1 小时前', read: false },
  { id: 3, title: '新增用户「王强」等待审批', type: 'info', time: '3 小时前', read: true },
  { id: 4, title: '系统将于今晚 23:00 进行维护升级', type: 'info', time: '昨天', read: true }
]

// 办件分类占比
export const caseCategoryData = [
  { name: '企业开办', value: 920 },
  { name: '社保参保', value: 780 },
  { name: '公积金提取', value: 640 },
  { name: '身份证办理', value: 580 },
  { name: '不动产登记', value: 460 },
  { name: '其他', value: 350 }
]
