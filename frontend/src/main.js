// 应用入口：挂载 Vue、Element Plus、路由与全局图标
import { createApp } from 'vue'
import {
  ElAlert,
  ElAside,
  ElAvatar,
  ElBadge,
  ElButton,
  ElCol,
  ElCollapse,
  ElCollapseItem,
  ElColorPicker,
  ElContainer,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElMain,
  ElOption,
  ElPagination,
  ElPopover,
  ElRadioButton,
  ElRadioGroup,
  ElRate,
  ElRow,
  ElSelect,
  ElStep,
  ElSteps,
  ElSwitch,
  ElTabPane,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTag
} from 'element-plus'
import 'element-plus/dist/index.css'
import {
  Document,
  Download,
  EditPen,
  List,
  Lock,
  OfficeBuilding,
  Plus,
  Postcard,
  Refresh,
  Search,
  Service,
  User
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

const elementComponents = [
  ElAlert, ElAside, ElAvatar, ElBadge, ElButton, ElCol, ElCollapse, ElCollapseItem,
  ElColorPicker, ElContainer, ElDescriptions, ElDescriptionsItem, ElDialog, ElDrawer,
  ElDropdown, ElDropdownItem, ElDropdownMenu, ElEmpty, ElForm, ElFormItem, ElHeader,
  ElIcon, ElInput, ElInputNumber, ElMain, ElOption, ElPagination, ElPopover,
  ElRadioButton, ElRadioGroup, ElRate, ElRow, ElSelect, ElStep, ElSteps, ElSwitch,
  ElTabPane, ElTable, ElTableColumn, ElTabs, ElTag
]
elementComponents.forEach((component) => app.component(component.name, component))
app.use(ElLoading)

const elementIcons = {
  Document, Download, EditPen, List, Lock, OfficeBuilding,
  Plus, Postcard, Refresh, Search, Service, User
}
Object.entries(elementIcons).forEach(([name, component]) => app.component(name, component))

app.use(router)
app.mount('#app')
