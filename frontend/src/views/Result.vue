<template>
  <div style="background:var(--sand); min-height:100vh">

    <!-- ══════ 顶部导航 ══════ -->
    <header class="sticky top-0 z-40"
            style="background:rgba(250,247,242,0.92); backdrop-filter:blur(12px);
                   border-bottom:1px solid #ece8e2; box-shadow:0 1px 12px rgba(28,25,23,0.05)">
      <div class="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <button @click="router.push('/')"
                class="flex items-center gap-2 text-sm font-medium transition-colors"
                style="color:var(--ink-muted)"
                @mouseenter="(e:any)=>e.target.style.color='var(--terracotta)'"
                @mouseleave="(e:any)=>e.target.style.color='var(--ink-muted)'">
          ← 重新规划
        </button>

        <div class="font-display font-semibold text-lg flex items-center gap-2" style="color:var(--ink)">
          <span style="color:var(--terracotta)">{{ plan?.city }}</span>
          <span style="color:#c4bdb6">·</span>
          <span>{{ plan?.days.length }} 天行程</span>
        </div>

        <div class="flex items-center gap-2">
          <template v-if="!editMode">
            <button @click="editMode = true" class="btn-ghost text-xs">✏️ 编辑行程</button>
          </template>
          <template v-else>
            <button @click="cancelEdit" class="btn-ghost text-xs">取消</button>
            <button @click="saveEdit"
                    class="btn-primary text-xs"
                    style="padding:8px 16px">保存</button>
          </template>
          <button @click="exportPlan" class="btn-ghost text-xs">⬇ 导出</button>
        </div>
      </div>
    </header>

    <!-- 无数据 -->
    <div v-if="!plan" class="flex items-center justify-center" style="min-height:60vh">
      <div class="text-center">
        <div style="font-size:3rem;margin-bottom:1rem">😕</div>
        <p style="color:var(--ink-muted)">未找到行程数据</p>
        <button @click="router.push('/')" class="btn-primary mt-6" style="padding:10px 24px; font-size:14px">返回首页</button>
      </div>
    </div>

    <div v-else id="trip-plan-content" class="max-w-6xl mx-auto px-6 py-10 space-y-8">

      <!-- ══════ ① 概览横幅 ══════ -->
      <div class="card p-7 relative overflow-hidden" style="background:linear-gradient(135deg,#1c2b3a 0%,#2d4a5a 100%)">
        <div class="absolute inset-0 opacity-10"
             style="background:radial-gradient(ellipse at 70% 50%,#c2624a,transparent 60%)"/>
        <div class="relative grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
          <div v-for="stat in overviewStats" :key="stat.label" class="text-center">
            <div class="font-display text-3xl font-semibold mb-1" :style="'color:'+stat.color">
              {{ stat.value }}
            </div>
            <div class="text-xs tracking-widest uppercase" style="color:rgba(255,255,255,0.45)">
              {{ stat.label }}
            </div>
          </div>
        </div>
        <div v-if="plan.overall_suggestions"
             class="relative text-sm leading-relaxed px-4 py-3 rounded-xl"
             style="background:rgba(255,255,255,0.07); color:rgba(255,255,255,0.7)">
          <span style="color:#d4a84b">💡 </span>{{ plan.overall_suggestions }}
        </div>
      </div>

      <!-- ══════ ② 预算 ══════ -->
      <div v-if="plan.budget" class="card p-7">
        <h2 class="section-title mb-6">💰 预算明细</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          <div v-for="item in budgetItems" :key="item.label"
               class="rounded-2xl p-4 text-center"
               :style="'background:'+item.bg">
            <div class="font-display text-2xl font-semibold mb-1" :style="'color:'+item.color">
              ¥{{ item.value.toLocaleString() }}
            </div>
            <div class="text-xs" style="color:var(--ink-muted)">{{ item.label }}</div>
          </div>
        </div>
        <div class="rounded-2xl p-5 text-center" style="background:#fff5f0; border:1.5px dashed #f5c4b6">
          <div class="text-xs tracking-widest uppercase mb-1" style="color:var(--ink-muted)">预估总费用</div>
          <div class="font-display font-semibold" style="font-size:2.2rem; color:var(--terracotta)">
            ¥{{ plan.budget.total.toLocaleString() }}
          </div>
        </div>
      </div>

      <!-- ══════ ③ 高德地图 ══════ -->
      <div class="card p-7">
        <h2 class="section-title mb-5">🗺️ 景点地图</h2>
        <!-- 天数筛选 -->
        <div class="flex gap-2 mb-5 flex-wrap">
          <button @click="activeDay = null"
                  class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
                  :style="activeDay === null
                    ? 'background:var(--terracotta);color:white'
                    : 'background:white;color:var(--ink-muted);border:1.5px solid #e2dbd2'">
            全部
          </button>
          <button v-for="(day, i) in plan.days" :key="day.date"
                  @click="switchDay(i)"
                  class="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
                  :style="activeDay === i
                    ? 'background:var(--teal);color:white'
                    : 'background:white;color:var(--ink-muted);border:1.5px solid #e2dbd2'">
            Day {{ i+1 }}
          </button>
        </div>
        <div id="amap-container" />
        <!-- 图例 -->
        <div class="flex flex-wrap gap-3 mt-4 items-center">
          <div v-for="(day, i) in plan.days" :key="'leg'+i" class="flex items-center gap-1.5 text-xs" style="color:var(--ink-muted)">
            <span class="w-3 h-3 rounded-full inline-block" :style="'background:'+dayColors[i % dayColors.length]"/>
            Day {{ i+1 }}
          </div>
          <div class="flex items-center gap-1.5 text-xs ml-2" style="color:var(--ink-muted); border-left:1px solid #e2dbd2; padding-left:12px">
            <span class="inline-flex items-center justify-center w-4 h-4 rounded text-white text-xs font-bold" style="background:#7c3aed; font-size:9px">H</span>
            酒店
          </div>
        </div>
      </div>

      <!-- ══════ ④ 天气 ══════ -->
      <div v-if="plan.weather_info.length" class="card p-7">
        <h2 class="section-title mb-5">🌤️ 旅途天气</h2>
        <div class="flex gap-3 overflow-x-auto pb-1">
          <div v-for="w in plan.weather_info" :key="w.date"
               class="flex-shrink-0 w-28 rounded-2xl p-4 text-center"
               style="background:var(--sand); border:1.5px solid #ece8e2">
            <div class="text-xs mb-2 font-medium" style="color:var(--ink-muted)">{{ w.date.slice(5) }}</div>
            <div class="text-2xl mb-1">{{ weatherIcon(w.day_weather) }}</div>
            <div class="text-sm font-medium" style="color:var(--ink)">{{ w.day_weather }}</div>
            <div class="text-xs mt-1.5 font-semibold" style="color:var(--terracotta)">
              {{ w.night_temp }}° / {{ w.day_temp }}°
            </div>
            <div class="text-xs mt-1" style="color:var(--ink-muted)">{{ w.wind_direction }}</div>
          </div>
        </div>
      </div>

      <!-- ══════ ⑤ 每日行程 ══════ -->
      <div>
        <h2 class="section-title mb-5">📅 每日行程</h2>
        <div class="space-y-5">
          <div v-for="(day, di) in plan.days" :key="day.date" class="card overflow-hidden">

            <!-- 日期头部 -->
            <div class="flex items-start gap-5 p-6"
                 :style="'background:'+dayColors[di%dayColors.length]+'14; border-bottom:1px solid '+dayColors[di%dayColors.length]+'22'">
              <div class="day-badge flex-shrink-0" :style="'background:'+dayColors[di%dayColors.length]">
                <span class="text-xs opacity-70 leading-none">Day</span>
                <span class="text-lg font-bold leading-none">{{ di+1 }}</span>
              </div>
              <div class="flex-1 pt-1">
                <div class="font-display font-semibold text-lg" style="color:var(--ink)">{{ day.date }}</div>
                <div class="text-sm mt-0.5" style="color:var(--ink-muted)">{{ day.description }}</div>
                <div class="flex items-center gap-4 mt-2 text-xs" style="color:var(--ink-muted)">
                  <span>🚇 {{ day.transportation }}</span>
                  <span v-if="day.hotel">🏨 {{ day.hotel.name }}</span>
                </div>
              </div>
            </div>

            <div class="p-6 space-y-6">

              <!-- 景点列表 -->
              <div>
                <div class="text-xs font-medium tracking-widest uppercase mb-3" style="color:var(--ink-muted)">景点安排</div>
                <div class="space-y-3">
                  <div v-for="(attr, ai) in day.attractions" :key="attr.name"
                       class="rounded-2xl overflow-hidden transition-colors"
                       style="border:1.5px solid #ece8e2; background:white">
                    <!-- 景点图片 -->
                    <div v-if="attr.image_url" class="relative h-36 overflow-hidden">
                      <img :src="attr.image_url" :alt="attr.name"
                           class="w-full h-full object-cover"
                           @error="(e:any) => e.target.style.display='none'" />
                      <!-- 序号浮层 -->
                      <div class="absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-md"
                           :style="'background:'+dayColors[di%dayColors.length]">
                        {{ ai+1 }}
                      </div>
                    </div>
                    <div class="flex gap-4 p-4">
                      <!-- 无图时显示序号 -->
                      <div v-if="!attr.image_url"
                           class="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold text-white"
                           :style="'background:'+dayColors[di%dayColors.length]">
                        {{ ai+1 }}
                      </div>
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 flex-wrap mb-1">
                          <span class="font-semibold" style="color:var(--ink)">{{ attr.name }}</span>
                          <span v-if="attr.rating"
                                class="text-xs px-2 py-0.5 rounded-full font-medium"
                                style="background:#fefce8; color:#a16207">⭐ {{ attr.rating }}</span>
                          <span v-if="attr.ticket_price !== undefined && attr.ticket_price > 0"
                                class="text-xs" style="color:var(--ink-muted)">🎫 ¥{{ attr.ticket_price }}</span>
                          <span class="text-xs" style="color:var(--ink-muted)">🕐 {{ attr.visit_duration }}分钟</span>
                        </div>
                        <div v-if="attr.address" class="text-xs mb-1 truncate" style="color:var(--ink-muted)">📍 {{ attr.address }}</div>
                        <div v-if="attr.description" class="text-sm leading-relaxed" style="color:#57534e">
                          {{ attr.description }}
                        </div>
                      </div>
                      <!-- 编辑按钮 -->
                      <div v-if="editMode" class="flex flex-col gap-1 flex-shrink-0">
                        <button @click="moveAttr(di,ai,'up')" :disabled="ai===0"
                                class="w-7 h-7 rounded-lg text-xs transition-colors flex items-center justify-center"
                                style="background:#f5f5f4; color:var(--ink-muted)"
                                :style="ai===0?'opacity:0.3':''">▲</button>
                        <button @click="moveAttr(di,ai,'down')" :disabled="ai===day.attractions.length-1"
                                class="w-7 h-7 rounded-lg text-xs transition-colors flex items-center justify-center"
                                style="background:#f5f5f4; color:var(--ink-muted)"
                                :style="ai===day.attractions.length-1?'opacity:0.3':''">▼</button>
                        <button @click="deleteAttr(di,ai)"
                                class="w-7 h-7 rounded-lg text-xs flex items-center justify-center"
                                style="background:#fff5f5; color:#dc2626">✕</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 餐饮 -->
              <div v-if="day.meals.length">
                <div class="text-xs font-medium tracking-widest uppercase mb-3" style="color:var(--ink-muted)">餐饮安排</div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div v-for="meal in day.meals" :key="meal.type"
                       class="flex items-start gap-3 p-4 rounded-2xl"
                       style="background:#fffbeb; border:1.5px solid #fde68a">
                    <span class="text-xl flex-shrink-0">{{ mealIcon(meal.type) }}</span>
                    <div class="min-w-0">
                      <div class="text-xs font-medium mb-0.5" style="color:#92400e">{{ mealLabel(meal.type) }}</div>
                      <div class="text-sm font-semibold truncate" style="color:var(--ink)">{{ meal.name }}</div>
                      <div v-if="meal.description" class="text-xs mt-0.5" style="color:var(--ink-muted)">{{ meal.description }}</div>
                      <div v-if="meal.estimated_cost" class="text-xs mt-1" style="color:var(--gold)">约 ¥{{ meal.estimated_cost }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 酒店 -->
              <div v-if="day.hotel"
                   class="flex items-center gap-4 p-4 rounded-2xl"
                   style="background:#f5f0ff; border:1.5px solid #e9d5ff">
                <span class="text-2xl flex-shrink-0">🏨</span>
                <div class="flex-1">
                  <div class="font-semibold" style="color:var(--ink)">{{ day.hotel.name }}</div>
                  <div v-if="day.hotel.address" class="text-xs mt-0.5" style="color:var(--ink-muted)">{{ day.hotel.address }}</div>
                  <div class="flex items-center gap-3 mt-1 text-xs" style="color:var(--ink-muted)">
                    <span v-if="day.hotel.rating">⭐ {{ day.hotel.rating }}</span>
                    <span v-if="day.hotel.price_range">💰 {{ day.hotel.price_range }}</span>
                    <span v-if="day.hotel.distance">📍 {{ day.hotel.distance }}</span>
                  </div>
                </div>
                <div v-if="day.hotel.estimated_cost" class="text-right flex-shrink-0">
                  <div class="font-display font-semibold" style="color:#7c3aed; font-size:1.1rem">
                    ¥{{ day.hotel.estimated_cost }}
                  </div>
                  <div class="text-xs" style="color:var(--ink-muted)">/ 晚</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>

      <!-- footer -->
      <div class="text-center text-xs pb-8" style="color:#c4bdb6">
        由 qwen3.6-plus · LangGraph 多智能体 · 高德地图 生成
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { TripPlan } from '../types'

declare const AMap: any

const router = useRouter()
const plan = ref<TripPlan | null>(null)
const editMode = ref(false)
let originalPlan = ''

const dayColors = ['#c2624a','#2d6a6a','#b5882a','#5b6abf','#7c8a3e','#a05484']
const activeDay = ref<number | null>(null)

let mapInstance: any = null
const markers: any[] = []
const polylines: any[] = []

// ── 初始化 ──
onMounted(() => {
  const raw = (history.state as any)?.tripPlan
  if (raw) {
    plan.value = JSON.parse(raw)
    originalPlan = raw
    nextTick(() => initMap())
  }
})

onUnmounted(() => {
  if (mapInstance) mapInstance.destroy()
})

// ── 地图 ──
function initMap() {
  if (typeof AMap === 'undefined' || !plan.value) return

  const container = document.getElementById('amap-container')
  if (!container) return

  // 计算地图中心（所有有坐标的景点 + 酒店的平均值）
  const allCoords = plan.value.days.flatMap(d => [
    ...d.attractions.filter(a => a.location).map(a => a.location!),
    ...(d.hotel?.location ? [d.hotel.location] : []),
  ])
  const center = allCoords.length
    ? [
        allCoords.reduce((s, c) => s + c.longitude, 0) / allCoords.length,
        allCoords.reduce((s, c) => s + c.latitude,  0) / allCoords.length,
      ]
    : [116.397, 39.909]

  mapInstance = new AMap.Map('amap-container', {
    zoom: 12,
    center,
    mapStyle: 'amap://styles/whitesmoke',
  })

  renderMarkers(null)
}

function renderMarkers(dayFilter: number | null) {
  if (!mapInstance || !plan.value) return

  // 清除旧标记和路线
  markers.forEach(m => m.setMap(null))
  polylines.forEach(p => p.setMap(null))
  markers.length = 0
  polylines.length = 0

  const daysToRender = dayFilter !== null
    ? [plan.value.days[dayFilter]]
    : plan.value.days

  daysToRender.forEach((day, relIdx) => {
    const realIdx = dayFilter !== null ? dayFilter : relIdx
    const color = dayColors[realIdx % dayColors.length]
    const coords: [number, number][] = []

    day.attractions.forEach((attr, ai) => {
      if (!attr.location) return
      const { longitude: lng, latitude: lat } = attr.location
      coords.push([lng, lat])

      // 自定义标记
      const marker = new AMap.Marker({
        position: [lng, lat],
        content: `<div style="
          width:32px;height:32px;border-radius:50%;
          background:${color};color:white;
          display:flex;align-items:center;justify-content:center;
          font-size:13px;font-weight:bold;
          box-shadow:0 3px 10px rgba(0,0,0,0.25);
          border:2.5px solid white;
          font-family:DM Sans,sans-serif;
        ">${ai + 1}</div>`,
        offset: new AMap.Pixel(-16, -16),
      })

      // 信息窗口
      const info = new AMap.InfoWindow({
        content: `<div style="padding:8px 12px;font-family:DM Sans,Noto Sans SC,sans-serif;min-width:160px">
          <div style="font-weight:600;font-size:14px;color:#1c1917;margin-bottom:4px">${attr.name}</div>
          ${attr.address ? `<div style="font-size:12px;color:#78716c">📍 ${attr.address}</div>` : ''}
          ${attr.ticket_price ? `<div style="font-size:12px;color:#78716c">🎫 ¥${attr.ticket_price}</div>` : ''}
        </div>`,
        offset: new AMap.Pixel(0, -34),
      })

      marker.on('click', () => info.open(mapInstance, [lng, lat]))
      marker.setMap(mapInstance)
      markers.push(marker)
    })

    // 连线
    if (coords.length > 1) {
      const poly = new AMap.Polyline({
        path: coords,
        strokeColor: color,
        strokeWeight: 3,
        strokeOpacity: 0.7,
        strokeStyle: 'dashed',
        lineJoin: 'round',
      })
      poly.setMap(mapInstance)
      polylines.push(poly)
    }

    // 酒店标记（仅在该天酒店有坐标且与前一天不同时显示，避免重复）
    if (day.hotel?.location) {
      const { longitude: hlng, latitude: hlat } = day.hotel.location
      const prevDayHotelName = realIdx > 0 ? daysToRender[realIdx - 1]?.hotel?.name : null
      const isDifferentHotel = day.hotel.name !== prevDayHotelName
      // 全部显示时：只在酒店换了或第一天时打标；单天筛选时：总是显示
      if (dayFilter !== null || isDifferentHotel || realIdx === 0) {
        const hotelMarker = new AMap.Marker({
          position: [hlng, hlat],
          content: `<div style="
            width:34px;height:34px;border-radius:8px;
            background:#7c3aed;color:white;
            display:flex;align-items:center;justify-content:center;
            font-size:14px;font-weight:bold;
            box-shadow:0 3px 10px rgba(124,58,237,0.45);
            border:2.5px solid white;
            font-family:DM Sans,sans-serif;
          ">H</div>`,
          offset: new AMap.Pixel(-17, -17),
          zIndex: 200,
        })

        const hotelInfo = new AMap.InfoWindow({
          content: `<div style="padding:8px 12px;font-family:DM Sans,Noto Sans SC,sans-serif;min-width:180px">
            <div style="font-weight:600;font-size:14px;color:#1c1917;margin-bottom:4px">🏨 ${day.hotel.name}</div>
            ${day.hotel.address ? `<div style="font-size:12px;color:#78716c">📍 ${day.hotel.address}</div>` : ''}
            ${day.hotel.price_range ? `<div style="font-size:12px;color:#78716c">💰 ${day.hotel.price_range}</div>` : ''}
            ${day.hotel.rating ? `<div style="font-size:12px;color:#78716c">⭐ ${day.hotel.rating}</div>` : ''}
            ${day.hotel.distance ? `<div style="font-size:12px;color:#78716c">📏 ${day.hotel.distance}</div>` : ''}
            <div style="font-size:11px;color:#a8a29e;margin-top:4px">Day ${realIdx + 1} 住宿</div>
          </div>`,
          offset: new AMap.Pixel(0, -36),
        })

        hotelMarker.on('click', () => hotelInfo.open(mapInstance, [hlng, hlat]))
        hotelMarker.setMap(mapInstance)
        markers.push(hotelMarker)
      }
    }
  })

  // 自适应视野
  if (markers.length) {
    mapInstance.setFitView(markers, false, [60, 60, 60, 60])
  }
}

function switchDay(i: number) {
  activeDay.value = activeDay.value === i ? null : i
  renderMarkers(activeDay.value)
}

watch(activeDay, val => renderMarkers(val))

// ── 统计 ──
const overviewStats = computed(() => {
  if (!plan.value) return []
  const total = plan.value.budget?.total
  return [
    { label: '天', value: plan.value.days.length, color: '#d4a84b' },
    { label: '景点', value: plan.value.days.reduce((s,d)=>s+d.attractions.length,0), color: '#7dd3b0' },
    { label: '预算(元)', value: total ? `¥${total.toLocaleString()}` : '—', color: '#f0a882' },
    { label: '出发', value: plan.value.start_date.slice(5), color: '#a5c8ea' },
  ]
})

const budgetItems = computed(() => {
  const b = plan.value?.budget
  if (!b) return []
  return [
    { label: '景点门票', value: b.total_attractions, bg: '#eff6ff', color: '#2563eb' },
    { label: '酒店住宿', value: b.total_hotels,      bg: '#f5f0ff', color: '#7c3aed' },
    { label: '餐饮费用', value: b.total_meals,        bg: '#fffbeb', color: '#b45309' },
    { label: '交通费用', value: b.total_transportation, bg: '#f0fdf4', color: '#16a34a' },
  ]
})

function weatherIcon(w: string) {
  if (w.includes('晴')) return '☀️'
  if (w.includes('云') || w.includes('阴')) return '⛅'
  if (w.includes('雨')) return '🌧️'
  if (w.includes('雪')) return '❄️'
  if (w.includes('雾')) return '🌫️'
  return '🌤️'
}

function mealIcon(t: string) {
  return { breakfast:'🌅', lunch:'☀️', dinner:'🌙', snack:'🍡' }[t] ?? '🍽️'
}
function mealLabel(t: string) {
  return { breakfast:'早餐', lunch:'午餐', dinner:'晚餐', snack:'小吃' }[t] ?? t
}

// ── 编辑 ──
function cancelEdit() {
  if (originalPlan) plan.value = JSON.parse(originalPlan)
  editMode.value = false
  nextTick(() => renderMarkers(activeDay.value))
}
function saveEdit() {
  originalPlan = JSON.stringify(plan.value)
  editMode.value = false
  nextTick(() => renderMarkers(activeDay.value))
}
function moveAttr(di: number, ai: number, dir: 'up'|'down') {
  const arr = plan.value!.days[di].attractions
  const ni = dir === 'up' ? ai-1 : ai+1
  if (ni >= 0 && ni < arr.length) [arr[ai], arr[ni]] = [arr[ni], arr[ai]]
}
function deleteAttr(di: number, ai: number) {
  plan.value!.days[di].attractions.splice(ai, 1)
  nextTick(() => renderMarkers(activeDay.value))
}

// ── 导出 ──
async function exportPlan() {
  try {
    const { default: html2canvas } = await import('html2canvas')
    const el = document.getElementById('trip-plan-content')!
    const canvas = await html2canvas(el, { scale: 1.5, useCORS: true, backgroundColor: '#faf7f2' })
    const a = document.createElement('a')
    a.download = `${plan.value?.city}_旅行计划.png`
    a.href = canvas.toDataURL('image/png')
    a.click()
  } catch {
    alert('导出失败，请确认 html2canvas 已安装')
  }
}
</script>
