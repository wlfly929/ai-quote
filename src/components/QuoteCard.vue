<!-- src/components/QuoteCard.vue -->
<template>
  <section v-if="quote" class="quote-section">
    <div class="quote-card">
      <p class="quote-text">{{ quote }}</p>
      <button 
        @click="toggleFavorite" 
        class="favorite-toggle-btn"
        :class="{ favorited: isFavorited }"
      >
        {{ isFavorited ? '❤️ 已收藏' : '🤍 收藏' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
// ============================================
// 1. 定义父组件传过来的数据（props）
// ============================================
defineProps<{
  quote: string
  isFavorited: boolean
}>()

// ============================================
// 2. 定义要发给父组件的事件（emits）
// ============================================
const emit = defineEmits<{
  (e: 'toggle-favorite'): void
}>()

// ============================================
// 3. 点击收藏按钮时，通知父组件
// ============================================
const toggleFavorite = () => {
  emit('toggle-favorite')
}
</script>

<style scoped>
/* 名言展示卡片 - 样式从 App.vue 迁移过来 */
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
</style>