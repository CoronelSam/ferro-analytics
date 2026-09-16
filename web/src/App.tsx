import { Route, Routes } from 'react-router-dom'
import { Layout } from './componentes/Layout'
import { Dashboard } from './paginas/Dashboard'
import { Inventario } from './paginas/Inventario'
import { Movimientos } from './paginas/Movimientos'
import { Reportes } from './paginas/Reportes'
import { Alertas } from './paginas/Alertas'
import { Importar } from './paginas/Importar'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="inventario" element={<Inventario />} />
        <Route path="movimientos" element={<Movimientos />} />
        <Route path="reportes" element={<Reportes />} />
        <Route path="alertas" element={<Alertas />} />
        <Route path="importar" element={<Importar />} />
      </Route>
    </Routes>
  )
}

export default App
