<template>
  <div class="min-h-screen" style="background:var(--sand)">

    <!-- ══════════ HERO ══════════ -->
    <div class="relative overflow-hidden" style="background:#1c2b3a; min-height: 380px;">
      <!-- 背景装饰 -->
      <div class="absolute inset-0 opacity-20"
           style="background: radial-gradient(ellipse 80% 60% at 60% 40%, #c2624a 0%, transparent 60%),
                             radial-gradient(ellipse 50% 50% at 20% 80%, #2d6a6a 0%, transparent 60%)" />
      <div class="absolute bottom-0 left-0 right-0 h-24"
           style="background: linear-gradient(to top, var(--sand), transparent)" />

      <!-- 装饰圆 -->
      <div class="absolute top-8 right-12 w-48 h-48 rounded-full opacity-5"
           style="border: 40px solid white" />
      <div class="absolute -bottom-8 left-1/4 w-32 h-32 rounded-full opacity-5"
           style="border: 20px solid white" />

      <div class="relative max-w-5xl mx-auto px-6 pt-16 pb-24 text-center">
        <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium mb-8 tracking-widest uppercase"
             style="background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); border: 1px solid rgba(255,255,255,0.15)">
          ✦ LangGraph 多智能体驱动
        </div>
        <h1 class="font-display mb-4" style="font-size:clamp(2.4rem,6vw,4rem); font-weight:600; color:white; line-height:1.1; letter-spacing:-0.02em">
          把旅行交给<br>
          <em style="color:#d4a84b; font-style:italic">智能助手</em>来安排
        </h1>
        <p class="text-base max-w-md mx-auto" style="color:rgba(255,255,255,0.55); line-height:1.7">
          描述你的想法，AI 自动规划景点路线、天气住宿和预算明细
        </p>
      </div>
    </div>

    <!-- ══════════ FORM CARD ══════════ -->
    <div class="max-w-2xl mx-auto px-4 pb-20" style="margin-top: -2px">

      <!-- Planning overlay -->
      <Transition name="slide-up">
        <div v-if="stage === 'planning'" class="card p-10 text-center">
          <div class="relative w-24 h-24 mx-auto mb-8">
            <svg class="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
              <circle cx="48" cy="48" r="40" fill="none" stroke="#ece8e2" stroke-width="6"/>
              <circle cx="48" cy="48" r="40" fill="none" stroke="#c2624a" stroke-width="6"
                stroke-dasharray="251.2" :stroke-dashoffset="251.2 * (1 - progress/100)"
                style="transition: stroke-dashoffset 0.8s ease"/>
            </svg>
            <span class="absolute inset-0 flex items-center justify-center text-3xl">✈️</span>
          </div>

          <h2 class="font-display mb-2" style="font-size:1.6rem; font-weight:600">正在规划中…</h2>
          <p class="text-sm mb-8" style="color:var(--ink-muted)">{{ statusText }}</p>

          <!-- Agent cards -->
          <div class="grid grid-cols-2 gap-3 mb-6">
            <div v-for="a in agents" :key="a.name"
                 class="p-4 rounded-2xl text-sm transition-all duration-500"
                 :style="a.done
                   ? 'background:#f0fdf4; border:1.5px solid #bbf7d0'
                   : 'background:var(--sand); border:1.5px solid #ece8e2'">
              <div class="text-2xl mb-2">{{ a.icon }}</div>
              <div class="font-medium text-xs" style="color:var(--ink)">{{ a.name }}</div>
              <div class="text-xs mt-1" :style="a.done ? 'color:#16a34a' : 'color:var(--ink-muted)'">
                {{ a.done ? '✓ 完成' : '运行中…' }}
              </div>
            </div>
          </div>

          <div class="text-xs" style="color:var(--ink-muted)">多智能体协作规划，请稍候 1~2 分钟</div>
        </div>
      </Transition>

      <!-- Form -->
      <Transition name="slide-up">
        <form v-if="stage !== 'planning'" @submit.prevent="handleSubmit" class="card p-8">

          <div class="mb-8">
            <h2 class="font-display mb-1" style="font-size:1.5rem; font-weight:600">填写旅行信息</h2>
            <p class="text-sm" style="color:var(--ink-muted)">填写越详细，行程越贴合你的需求</p>
          </div>

          <!-- 目的地 + 天数 -->
          <div class="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">
                目的地 <span style="color:var(--terracotta)">*</span>
              </label>
              <input v-model="form.city" class="input-field" placeholder="北京、上海、成都…" required />
            </div>
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">
                旅行天数 <span style="color:var(--terracotta)">*</span>
              </label>
              <select v-model.number="form.days" class="input-field">
                <option v-for="d in [1,2,3,4,5,6,7]" :key="d" :value="d">{{ d }} 天</option>
              </select>
            </div>
          </div>

          <!-- 日期 -->
          <div class="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">出发日期</label>
              <input v-model="form.start_date" type="date" class="input-field" :min="today" required />
            </div>
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">返回日期</label>
              <input v-model="form.end_date" type="date" class="input-field" :min="form.start_date || today" required />
            </div>
          </div>

          <!-- 偏好（多选） -->
          <div class="mb-5">
            <label class="block text-xs font-medium mb-3 tracking-wide uppercase" style="color:var(--ink-muted)">
              旅行偏好
              <span style="color:#c4bdb6; font-weight:400; text-transform:none; letter-spacing:0">（可多选）</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <button v-for="p in prefOptions" :key="p.value" type="button"
                      @click="togglePref(p.value)"
                      class="px-4 py-2 rounded-full text-sm transition-all duration-150 font-medium"
                      :style="selectedPrefs.includes(p.value)
                        ? 'background:var(--terracotta); color:white; border:1.5px solid var(--terracotta)'
                        : 'background:white; color:var(--ink-muted); border:1.5px solid #e2dbd2'">
                {{ p.icon }} {{ p.label }}
              </button>
            </div>
          </div>

          <!-- 预算 + 交通 + 住宿 -->
          <div class="grid grid-cols-3 gap-3 mb-7">
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">预算</label>
              <select v-model="form.budget" class="input-field text-sm">
                <option value="经济">💰 经济</option>
                <option value="中等">💳 中等</option>
                <option value="豪华">💎 豪华</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">交通</label>
              <select v-model="form.transportation" class="input-field text-sm">
                <option value="公共交通">🚇 地铁公交</option>
                <option value="自驾">🚗 自驾</option>
                <option value="打车">🚕 打车</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">住宿</label>
              <select v-model="form.accommodation" class="input-field text-sm">
                <option value="经济型酒店">🏨 经济型</option>
                <option value="商务酒店">🏢 商务型</option>
                <option value="豪华酒店">⭐ 豪华型</option>
                <option value="民宿">🏡 民宿</option>
              </select>
            </div>
          </div>

          <!-- 额外要求 -->
          <div class="mb-7">
            <label class="block text-xs font-medium mb-2 tracking-wide uppercase" style="color:var(--ink-muted)">
              额外要求 <span style="color:#c4bdb6">（可选）</span>
            </label>
            <textarea v-model="form.extra_requirements"
                      class="input-field resize-none"
                      rows="3"
                      placeholder="例：不想爬山、需要无障碍设施、对海鲜过敏、希望避开人流高峰…" />
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMsg"
               class="mb-5 px-4 py-3 rounded-xl text-sm flex items-start gap-2"
               style="background:#fff5f5; border:1.5px solid #fecaca; color:#dc2626">
            <span>⚠</span><span>{{ errorMsg }}</span>
          </div>

          <!-- 提交 -->
          <button type="submit" class="btn-primary w-full justify-center text-base" style="padding:14px">
            <span style="font-size:1.1em">✈</span>
            <span>开始规划</span>
          </button>

          <p class="text-center text-xs mt-4" style="color:#c4bdb6">
            qwen3.6-plus · LangGraph 多智能体 · 高德地图数据
          </p>
        </form>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { generateTripPlan } from '../services/api'
import type { TripPlanRequest, PlanningStage } from '../types'

const router = useRouter()
const stage = ref<PlanningStage>('idle')
const errorMsg = ref('')
const progress = ref(0)
const today = new Date().toISOString().split('T')[0]

const form = ref<TripPlanRequest>({
  city: '', start_date: today, end_date: '',
  days: 3, preferences: '历史文化', budget: '中等',
  transportation: '公共交通', accommodation: '经济型酒店', extra_requirements: '',
})

watch(() => [form.value.start_date, form.value.days], ([start, days]) => {
  if (start) {
    const d = new Date(start as string)
    d.setDate(d.getDate() + (days as number) - 1)
    form.value.end_date = d.toISOString().split('T')[0]
  }
}, { immediate: true })

const prefOptions = [
  { value: '历史文化', label: '历史文化', icon: '🏛️' },
  { value: '自然风光', label: '自然风光', icon: '🌿' },
  { value: '美食探索', label: '美食探索', icon: '🍜' },
  { value: '购物娱乐', label: '购物娱乐', icon: '🛍️' },
  { value: '亲子游',   label: '亲子游',   icon: '👨‍👩‍👧' },
  { value: '休闲度假', label: '休闲度假', icon: '🏖️' },
  { value: '摄影打卡', label: '摄影打卡', icon: '📸' },
]

const selectedPrefs = ref<string[]>(['历史文化'])

function togglePref(value: string) {
  const idx = selectedPrefs.value.indexOf(value)
  if (idx === -1) {
    selectedPrefs.value.push(value)
  } else if (selectedPrefs.value.length > 1) {
    // 至少保留一项
    selectedPrefs.value.splice(idx, 1)
  }
}

const agents = ref([
  { name: '景点搜索', icon: '🏛️', node: 'attraction_search', done: false },
  { name: '天气查询', icon: '🌤️', node: 'weather_query',     done: false },
  { name: '酒店推荐', icon: '🏨', node: 'hotel_search',      done: false },
  { name: '行程规划', icon: '📋', node: 'planner',           done: false },
])

const NODE_PROGRESS: Record<string, number> = {
  attraction_search: 25,
  weather_query:     35,
  hotel_search:      65,
  planner:           95,
}

const NODE_STATUS: Record<string, string> = {
  attraction_search: '🏛️ 景点搜索完成，开始分析酒店位置…',
  weather_query:     '🌤️ 天气数据已就绪',
  hotel_search:      '🏨 酒店推荐完成，正在生成行程…',
  planner:           '📋 行程规划完成，处理图片中…',
}

const statusText = ref('多智能体启动中…')

function handleNodeDone(node: string) {
  const agent = agents.value.find(a => a.node === node)
  if (agent) agent.done = true
  if (NODE_PROGRESS[node]) progress.value = NODE_PROGRESS[node]
  if (NODE_STATUS[node])   statusText.value = NODE_STATUS[node]
}

function resetProgress() {
  progress.value = 5
  statusText.value = '多智能体启动中…'
  agents.value.forEach(a => (a.done = false))
}

async function handleSubmit() {
  if (!form.value.city.trim()) return
  errorMsg.value = ''
  stage.value = 'planning'
  resetProgress()
  try {
    const result = await generateTripPlan(
      { ...form.value, preferences: selectedPrefs.value.join('、') },
      handleNodeDone,
    )
    progress.value = 100
    agents.value.forEach(a => (a.done = true))
    router.push({ name: 'result', state: { tripPlan: JSON.stringify(result) } })
  } catch (e: any) {
    errorMsg.value = e?.message || '规划失败，请检查网络后重试'
    stage.value = 'idle'
  }
}
</script>

<style scoped>
.slide-up-enter-active { transition: all 0.4s cubic-bezier(0.16,1,0.3,1); }
.slide-up-leave-active { transition: all 0.25s ease; }
.slide-up-enter-from  { opacity: 0; transform: translateY(16px); }
.slide-up-leave-to    { opacity: 0; transform: translateY(-8px); }
</style>
