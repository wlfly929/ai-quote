<template>
  <div class="app-container">
    <header class="app-header">
      <h1 class="title">✨ AI 灵感名言</h1>
    </header>

    <div class="content-wrapper">
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

      <QuoteCard 
        :quote="quote" 
        :is-favorited="isCurrentFavorited"
        @toggle-favorite="toggleFavorite"
      />

      <section v-if="favorites.length > 0" class="favorites-section">
        <h2 class="favorites-title">📌 我的收藏</h2>
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

      <section v-else-if="!quote && !loading" class="empty-state">
        <p>💡 输入一个主题，开始探索名言吧</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import QuoteCard from './components/QuoteCard.vue'

// ========== 数据 ==========
const topic = ref('')
const quote = ref('')
const loading = ref(false)
const favorites = ref<string[]>([])

// ========== AI 接口 ==========
const API_KEY = import.meta.env.VITE_API_KEY 
const API_URL = 'https://api.deepseek.com/v1/chat/completions'

// ========== 判断是否已收藏 ==========
const isCurrentFavorited = computed(() => {
  return quote.value && favorites.value.includes(quote.value)
})

// ========== 从后端加载收藏 ==========
const loadFavorites = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/favorites')
    const data = await res.json()
    favorites.value = data.map((item: any) => item.content)
  } catch (e) {
    console.error('加载收藏失败:', e)
    favorites.value = []
  }
}

// ========== 删除收藏 ==========
const removeFavorite = async (index: number) => {
  const content = favorites.value[index]
  try {
    const res = await fetch('http://127.0.0.1:8000/favorites')
    const all = await res.json()
    const target = all.find((item: any) => item.content === content)
    if (target) {
      await fetch(`http://127.0.0.1:8000/favorites/${target.id}`, {
        method: 'DELETE'
      })
    }
    await loadFavorites()
  } catch (e) {
    console.error('删除收藏失败:', e)
  }
}

// ========== 切换收藏状态 ==========
const toggleFavorite = async () => {
  if (!quote.value) return
  
  const index = favorites.value.indexOf(quote.value)
  
  if (index > -1) {
    // 取消收藏
    try {
      const res = await fetch('http://127.0.0.1:8000/favorites')
      const all = await res.json()
      const target = all.find((item: any) => item.content === quote.value)
      if (target) {
        await fetch(`http://127.0.0.1:8000/favorites/${target.id}`, {
          method: 'DELETE'
        })
      }
    } catch (e) {
      console.error('取消收藏失败:', e)
    }
  } else {
    // 添加收藏
    try {
      await fetch(`http://127.0.0.1:8000/favorites?content=${encodeURIComponent(quote.value)}`, {
        method: 'POST'
      })
    } catch (e) {
      console.error('添加收藏失败:', e)
    }
  }
  await loadFavorites()
}

// ========== 生成名言 ==========
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
        stream: true
      })
    })

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
      
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.replace('data: ', '').trim()
          if (jsonStr === '[DONE]') continue
          
          try {
            const json = JSON.parse(jsonStr)
            const content = json.choices?.[0]?.delta?.content || ''
            if (content) {
              quote.value += content
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

// ========== 组件挂载时加载收藏 ==========
onMounted(() => {
  loadFavorites()
})
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

.content-wrapper {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
  padding-bottom: 40px;
}

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

.empty-state {
  width: 100%;
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.1rem;
}
</style>

<style>
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>