import React from 'react';
import PropTypes from 'prop-types';

/**
 * 宠物卡片组件
 * 
 * 用于展示宠物的基本信息，包括名称、品种、年龄和照片
 * 
 * @param {Object} props - 组件属性
 * @param {string} props.name - 宠物名称
 * @param {string} props.breed - 宠物品种
 * @param {number} props.age - 宠物年龄（月）
 * @param {string} props.imageUrl - 宠物照片URL
 * @param {() => void} props.onClick - 点击卡片时的回调函数
 * @returns {JSX.Element} 宠物卡片组件
 */
const PetCard: React.FC<{
  name: string;
  breed: string;
  age: number;
  imageUrl: string;
  onClick: () => void;
}> = ({ name, breed, age, imageUrl, onClick }) => {
  return (
    <div 
      className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300 cursor-pointer"
      onClick={onClick}
    >
      <div className="h-48 overflow-hidden">
        <img 
          src={imageUrl} 
          alt={`${name}的照片`} 
          className="w-full h-full object-cover"
        />
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-800">{name}</h3>
        <p className="text-sm text-gray-600">{breed}</p>
        <p className="text-sm text-gray-500 mt-1">{age} 个月</p>
      </div>
    </div>
  );
};

// PropTypes 定义（虽然 TypeScript 已经提供了类型检查，但为了满足规范要求，仍然添加）
PetCard.propTypes = {
  name: PropTypes.string.isRequired,
  breed: PropTypes.string.isRequired,
  age: PropTypes.number.isRequired,
  imageUrl: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default PetCard; 