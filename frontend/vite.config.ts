import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // 您前端开发服务器的端口
    proxy: {
      // 字符串简写写法，将所有 /api 开头的请求代理到 http://localhost:8000
      // 例如：/api/generate-simple-p1 将被代理到 http://localhost:8000/api/generate-simple-p1
      // 注意：如果您的FastAPI后端路由本身不包含 /api 前缀（就像我们现在这样，Nginx会rewrite掉它），
      // 那么这里的代理也应该将 /api 去掉再转发，或者FastAPI端点需要能处理 /api 前缀。
      // 为了与Nginx部署时的行为保持一致（Nginx将 /api/... 转发为 /... 到后端），
      // 我们在这里也配置类似的路径重写。
      '/api': {
        target: 'http://localhost:8000', // 您本地FastAPI后端的地址
        changeOrigin: true, // 建议设置为true，对于某些服务器是必需的
        rewrite: (path) => path.replace(/^\/api/, ''), // 关键：将请求路径中的 /api 前缀去掉
                                                      // 这样，前端请求 /api/generate-simple-p1
                                                      // 会被代理到 http://localhost:8000/generate-simple-p1
      },
      // 如果您有其他需要代理的路径，可以在这里继续添加
      // 例如，如果未来有 /auth/login 等路径也需要代理到后端：
      // '/auth': {
      //   target: 'http://localhost:8000',
      //   changeOrigin: true,
      // }
    }
  }
})