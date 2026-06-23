<template>
  <div class="app-container">
    <!-- 顶部标题 -->
    <header class="app-header">
      <h1 class="title">✨ AI 灵感名言</h1>
    </header>

    <!-- 内容包装器 -->
    <div class="content-wrapper">
      <!-- 输入区域 -->
      <section class="input-section">
        <input 
          v-model="topic" 
          placeholder="输入主题，比如：坚持、梦想、勇气..." 
          @keyup.enter="getQuote"
          :disabled="loading"
          class="topic-input"
        />
        <button 
          @click="getQuote" 
          :disabled="loading || !topic.trim()"
          class="generate-btn"
        >
          {{ loading ? '生成中...' : '生成名言' }}
        </button>
      </section>

      <!-- 名言展示卡片 -->
  <!-- 名言展示卡片 - 使用子组件 -->
<QuoteCard 
  :quote="quote" 
  :is-favorited="isCurrentFavorited"
  @toggle-favorite="toggleFavorite"
/>

      <!-- 收藏列表 -->
      <section v-if="favorites.length > 0" class="favorites-section">
        <h2 class="favorites-title"> 我的收藏</h2>
        <div class="favorites-list">
          <div 
            v-for="(item, index) in favorites" 
            :key="index"
            class="favorite-card"
          >
            <span class="favorite-text">{{ item }}</span>
            <button 
              @click="removeFavorite(index)" 
              class="remove-btn"
              title="删除收藏"
            >
              ✕
            </button>
          </div>
        </div>
      </section>

      <!-- 空状态提示 -->
      <section v-else-if="!quote && !loading" class="empty-state">
        <p>💡 输入一个主题，开始探索名言吧</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import QuoteCard from './components/QuoteCard.vue'

// --- 1. 定义数据 ---
const topic = ref('')
const quote = ref('')
const loading = ref(false)
const favorites = ref<string[]>([])

// --- 2. 配置AI接口 ---
const API_KEY = import.meta.env.VITE_API_KEY 
const API_URL = 'https://api.deepseek.com/v1/chat/completions'

// --- 3. 判断当前名言是否已收藏 ---
const isCurrentFavorited = computed(() => {
  return quote.value && favorites.value.includes(quote.value)
})

// --- 4. 从 localStorage 加载收藏 ---
const loadFavorites = () => {
  const saved = localStorage.getItem('ai-quote-favorites')
  if (saved) {
    try {
      favorites.value = JSON.parse(saved)
    } catch (e) {
      console.error('加载收藏失败:', e)
      favorites.value = []
    }
  }
}

// --- 5. 保存收藏到 localStorage ---
const saveFavorites = () => {
  localStorage.setItem('ai-quote-favorites', JSON.stringify(favorites.value))
}

// --- 6. 监听收藏变化，自动保存 ---
watch(favorites, () => {
  saveFavorites()
}, { deep: true })

// --- 7. 组件挂载时加载收藏 ---
onMounted(() => {
  loadFavorites()
})

// --- 8. 删除收藏 ---
const removeFavorite = (index: number) => {
  favorites.value.splice(index, 1)
}

const getQuote = async () => {
  if (!topic.value.trim()) {
    alert('请输入一个主题')
    return
  }

  loading.value = true
  quote.value = ''

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: '你是一位名言专家,请用中文回复一句关于给定主题的励志名言,并附上作者。回复格式:名言内容 —— 作者名' },
          { role: 'user', content: `关于"${topic.value}"的名言` }
        ],
        stream: true  // ⬅️ 这里改成 true
      })
    })

    // 获取响应体的读取器
    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    
    if (!reader) {
      quote.value = '无法读取响应流'
      loading.value = false
      return
    }

    let buffer = ''
    let isDone = false

    while (!isDone) {
      const { done, value } = await reader.read()
      isDone = done
      
      if (done) break
      
      // 将数据块解码为文本
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      
      // 按行分割，处理 data: 开头的行
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留不完整的行
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.replace('data: ', '').trim()
          if (jsonStr === '[DONE]') continue
          
          try {
            const json = JSON.parse(jsonStr)
            const content = json.choices?.[0]?.delta?.content || ''
            if (content) {
              quote.value += content  // ⬅️ 逐字累加，实现打字机效果
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
  } catch (error) {
    console.error('请求失败:', error)
    quote.value = '网络请求失败,请检查网络或API Key是否正确'
  } finally {
    loading.value = false
  }
}

// --- 11. 切换收藏状态 ---
const toggleFavorite = () => {
  if (!quote.value) return
  
  const index = favorites.value.indexOf(quote.value)
  if (index > -1) {
    favorites.value.splice(index, 1)
  } else {
    favorites.value.unshift(quote.value)
  }
}
</script>

<style scoped>
/* 整体容器 - 深色渐变背景，全屏铺满 */
.app-container {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 40px 20px;
  background: linear-gradient(135deg, #1a1f3a 0%, #2d3748 50%, #1a202c 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* 内容包装器 - 用于垂直居中 */
.content-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  padding-bottom: 40px;
}

/* 顶部标题 */
.app-header {
  margin-bottom: 40px;
  margin-top: 20px;
  text-align: center;
  flex-shrink: 0;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

/* 输入区域 */
.input-section {
  width: 100%;
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
}

.topic-input {
  flex: 1;
  padding: 18px 24px;
  font-size: 1rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  color: #ffffff;
  outline: none;
  transition: all 0.3s ease;
}

.topic-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.topic-input:focus {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
}

.topic-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.generate-btn {
  padding: 18px 32px;
  font-size: 1rem;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.generate-btn:active:not(:disabled) {
  transform: scale(1.02);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 名言展示卡片 */
.quote-section {
  width: 100%;
  margin-bottom: 40px;
}

.quote-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.quote-text {
  font-size: 20px;
  line-height: 1.8;
  color: #ffffff;
  text-align: center;
  margin: 0;
  font-weight: 500;
}

.favorite-toggle-btn {
  padding: 12px 24px;
  font-size: 0.95rem;
  font-weight: 600;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.favorite-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.05);
}

.favorite-toggle-btn.favorited {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  color: #ff6b6b;
}

.favorite-toggle-btn.favorited:hover {
  background: rgba(239, 68, 68, 0.3);
}

/* 收藏列表区域 */
.favorites-section {
  width: 100%;
}

.favorites-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 24px;
  text-align: center;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.favorite-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.favorite-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateX(4px);
}

.favorite-text {
  flex: 1;
  font-size: 0.95rem;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.9);
  word-break: break-word;
}

.remove-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ff6b6b;
  transform: scale(1.1);
}

/* 空状态提示 */
.empty-state {
  width: 100%;
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.1rem;
}
</style>
/* 响应式设计 - 平板 */
@media (max-width: 1024px) {
  .app-container {
    padding: 30px 20px;
  }

  .title {
    font-size: 2rem;
  }

  .content-wrapper {
    gap: 30px;
  }

  .quote-card {
    padding: 30px;
  }

  .quote-text {
    font-size: 18px;
  }
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .app-container {
    padding: 20px 16px;
  }

  .title {
    font-size: 1.8rem;
  }

  .content-wrapper {
    gap: 24px;
  }

  .input-section {
    flex-direction: column;
  }

  .generate-btn {
    width: 100%;
  }

  .quote-card {
    padding: 24px;
  }

  .quote-text {
    font-size: 16px;
  }

  .favorites-title {
    font-size: 1.3rem;
  }

  .favorite-card {
    padding: 16px 20px;
  }

  .favorite-text {
    font-size: 0.9rem;
  }
}
<!-- 在现有的 <style scoped> 之后，添加这个全局样式块 -->
<style>
/* 全局样式重置，解决页面左侧空白和滚动条问题 */
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden; /* 禁止横向滚动 */
  box-sizing: border-box;
}

/* 确保 #app 根元素也占满全屏 */
#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>