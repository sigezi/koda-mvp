/**
 * 宠物类型枚举
 */
export enum PetSpecies {
  CAT = 'cat',
  DOG = 'dog',
  BIRD = 'bird',
  FISH = 'fish',
  OTHER = 'other',
}

/**
 * 宠物情绪类型枚举
 */
export enum EmotionType {
  HAPPY = 'happy',
  SAD = 'sad',
  ANGRY = 'angry',
  SCARED = 'scared',
  NEUTRAL = 'neutral',
  EXCITED = 'excited',
  ANXIOUS = 'anxious',
}

/**
 * 宠物日志类型枚举
 */
export enum LogType {
  HEALTH = 'health',
  FOOD = 'food',
  MOOD = 'mood',
  CHAT = 'chat',
}

/**
 * 宠物基本信息接口
 */
export interface Pet {
  id: string;
  name: string;
  species: PetSpecies;
  breed: string;
  age: number;
  weight: number;
  imageUrl: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 宠物日志接口
 */
export interface PetLog {
  id: string;
  petId: string;
  userId: string;
  logType: LogType;
  content: string;
  date: string;
  sentiment?: number;
  emotionType?: EmotionType;
  aiAnalysis?: string;
  createdAt: string;
}

/**
 * 宠物情绪统计接口
 */
export interface EmotionStats {
  mainEmotion: EmotionType;
  averageSentiment: number;
  emotionCounts: Record<EmotionType, number>;
}

/**
 * 宠物日常活动接口
 */
export interface PetRoutine {
  wakeUpTime: string;
  sleepTime: string;
  mealTimes: string[];
  activityTimes: string[];
  favoriteActivities: string[];
  favoriteFoods: string[];
} 