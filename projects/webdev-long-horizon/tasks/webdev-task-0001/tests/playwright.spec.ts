import { test, expect } from '@playwright/test';

test.describe('O2O 平台核心验收', () => {
  test('首页能加载并显示地图与商家列表', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=本地生活')).toBeVisible();
    // TODO: 断言地图容器与商家列表存在
  });

  test('筛选分类后列表更新', async ({ page }) => {
    await page.goto('/');
    // TODO: 点击分类筛选按钮，断言列表更新
  });

  test('点击商家卡片进入详情页', async ({ page }) => {
    await page.goto('/');
    // TODO: 点击第一个商家卡片，断言路由跳转到 /merchant/:id
  });

  test('详情页可加入购物车', async ({ page }) => {
    await page.goto('/merchant/m001');
    // TODO: 点击“加入购物车”，断言购物车中商品数量增加
  });

  test('购物车可提交订单', async ({ page }) => {
    await page.goto('/merchant/m001');
    // TODO: 加入商品，打开购物车，提交订单，断言跳转到 /order-success
  });

  test('空态显示正确', async ({ page }) => {
    await page.goto('/');
    // TODO: 触发无结果筛选，断言空态 UI
  });

  test('移动端菜单可交互', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    // TODO: 点击汉堡菜单，断言导航展开
  });
});
