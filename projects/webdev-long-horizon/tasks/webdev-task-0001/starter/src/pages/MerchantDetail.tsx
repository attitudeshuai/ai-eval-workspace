import { useParams } from 'react-router-dom';

export default function MerchantDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-bold text-gray-900">商家详情</h1>
      <p className="mt-2 text-gray-600">当前商家 ID: {id}</p>
      <p className="mt-4 text-gray-600">请实现商家头图、商品列表、路线规划与加入购物车功能。</p>
    </div>
  );
}
