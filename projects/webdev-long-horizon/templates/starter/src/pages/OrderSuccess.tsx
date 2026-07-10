export default function OrderSuccess() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white p-12 shadow-sm">
      <div className="mb-4 text-5xl text-green-500">✓</div>
      <h1 className="text-2xl font-bold text-gray-900">下单成功</h1>
      <p className="mt-2 text-gray-600">订单号：ORD-20260710-001</p>
      <p className="mt-4 text-gray-500">请根据任务需求实现动态订单号与返回首页入口。</p>
    </div>
  );
}
