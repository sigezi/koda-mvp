import { create, StateCreator } from 'zustand';
import { Pet, PetLog, EmotionStats } from '../types/pet';

/**
 * 宠物状态接口
 */
interface PetState {
  pets: Pet[];
  selectedPet: Pet | null;
  petLogs: PetLog[];
  emotionStats: EmotionStats | null;
  isLoading: boolean;
  error: string | null;
  
  // 动作
  setPets: (pets: Pet[]) => void;
  setSelectedPet: (pet: Pet | null) => void;
  setPetLogs: (logs: PetLog[]) => void;
  setEmotionStats: (stats: EmotionStats | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // 异步动作
  fetchPets: () => Promise<void>;
  fetchPetLogs: (petId: string) => Promise<void>;
  fetchEmotionStats: (petId: string) => Promise<void>;
  addPet: (pet: Omit<Pet, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updatePet: (pet: Pet) => Promise<void>;
  deletePet: (petId: string) => Promise<void>;
  addPetLog: (log: Omit<PetLog, 'id' | 'createdAt'>) => Promise<void>;
}

/**
 * 创建宠物状态管理 store
 */
export const usePetStore = create<PetState>((set, get) => ({
  // 初始状态
  pets: [],
  selectedPet: null,
  petLogs: [],
  emotionStats: null,
  isLoading: false,
  error: null,
  
  // 同步动作
  setPets: (pets: Pet[]) => set({ pets }),
  setSelectedPet: (pet: Pet | null) => set({ selectedPet: pet }),
  setPetLogs: (logs: PetLog[]) => set({ petLogs: logs }),
  setEmotionStats: (stats: EmotionStats | null) => set({ emotionStats: stats }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  
  // 异步动作
  fetchPets: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch('/api/pets');
      if (!response.ok) {
        throw new Error('获取宠物列表失败');
      }
      const pets = await response.json();
      set({ pets, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  fetchPetLogs: async (petId: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`/api/pets/${petId}/logs`);
      if (!response.ok) {
        throw new Error('获取宠物日志失败');
      }
      const logs = await response.json();
      set({ petLogs: logs, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  fetchEmotionStats: async (petId: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`/api/pets/${petId}/emotion-stats`);
      if (!response.ok) {
        throw new Error('获取情绪统计失败');
      }
      const stats = await response.json();
      set({ emotionStats: stats, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  addPet: async (pet: Omit<Pet, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch('/api/pets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pet),
      });
      if (!response.ok) {
        throw new Error('添加宠物失败');
      }
      const newPet = await response.json();
      set((state) => ({
        pets: [...state.pets, newPet],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  updatePet: async (pet: Pet) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`/api/pets/${pet.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pet),
      });
      if (!response.ok) {
        throw new Error('更新宠物信息失败');
      }
      const updatedPet = await response.json();
      set((state) => ({
        pets: state.pets.map((p) => (p.id === pet.id ? updatedPet : p)),
        selectedPet: state.selectedPet?.id === pet.id ? updatedPet : state.selectedPet,
        isLoading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  deletePet: async (petId: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`/api/pets/${petId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('删除宠物失败');
      }
      set((state) => ({
        pets: state.pets.filter((p) => p.id !== petId),
        selectedPet: state.selectedPet?.id === petId ? null : state.selectedPet,
        isLoading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
  
  addPetLog: async (log: Omit<PetLog, 'id' | 'createdAt'>) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`/api/pets/${log.petId}/logs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(log),
      });
      if (!response.ok) {
        throw new Error('添加宠物日志失败');
      }
      const newLog = await response.json();
      set((state) => ({
        petLogs: [...state.petLogs, newLog],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
})); 