function App() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Web Dev Task Starter</h1>
        <p className="mt-2 text-gray-600">
          请在 <code className="rounded bg-gray-200 px-1 py-0.5">task.md</code> 中阅读需求并开始实现。
        </p>
      </header>

      <main className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold">初始项目已就绪</h2>
        <ul className="list-inside list-disc space-y-2 text-gray-700">
          <li>React 18 + TypeScript + Vite</li>
          <li>Tailwind CSS 已配置</li>
          <li>Playwright 测试骨架已配置</li>
        </ul>
      </main>
    </div>
  );
}

export default App;
