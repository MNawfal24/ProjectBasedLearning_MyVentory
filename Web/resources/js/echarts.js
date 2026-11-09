import { use } from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// Only the pieces the dashboard draws are registered, so the bundle stays small.
use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

export { default as VChart } from 'vue-echarts';
