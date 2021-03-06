<script lang="ts">
import VisTileLarge from '@/components/vis/VisTileLarge.vue';
import LayoutGrid from '@/components/LayoutGrid.vue';
import {
  computed, ComputedRef, defineComponent, reactive, toRef, watch, watchEffect,
} from '@vue/composition-api';
import ScorePlot from './ScorePlot.vue';
import LoadingsPlot from './LoadingsPlot.vue';
import VipPlot from './VipPlot.vue';
import usePlotData from '../use/usePlotData';
import store from '../../../store';
import { downloadCSV } from '../../../utils/exporter';

export default defineComponent({
  props: {
    id: {
      type: String,
      required: true,
    },
  },
  components: {
    ScorePlot,
    LoadingsPlot,
    VipPlot,
    VisTileLarge,
    LayoutGrid,
  },
  setup(props) {
    const { dataset, plot, changePlotArgs } = usePlotData(toRef(props, 'id'), 'plsda');
    const controls = reactive({
      pcXval: '1',
      pcYval: '2',
      numComponentsVal: '3',
      pcX: 1,
      pcY: 2,
      numComponents: 3,
      showEllipses: true,
      showCrosshairs: true,
      showCutoffs: true,
      showScore: true,
      showLoadings: true,
      showVip: true,
      vipComponentVal: '1',
      vipComponent: 1,
      sortVip: false,
    });

    const ready = computed(() => {
      const pcaReady = store.getters.ready(props.id, 'plsda_scores');
      const loadingsReady = store.getters.ready(props.id, 'plsda_loadings');
      return pcaReady && loadingsReady;
    });
    const r2: ComputedRef<number[]> = computed(() => plot.value.data?.r2 || []);
    const q2: ComputedRef<number[]> = computed(() => plot.value.data?.q2 || []);
    const r2q2Table = computed(() => r2.value.map((r2Val, i) => ({ name: `PC${i + 1}`, r2: r2Val.toFixed(3), q2: q2.value[i].toFixed(3) })));
    const r2cum = computed(() => r2.value.reduce((a, b) => a + b, 0).toFixed(3));
    const q2cum = computed(() => q2.value.reduce((a, b) => a + b, 0).toFixed(3));
    const loadings = computed(() => plot.value.data?.loadings || []);
    const allVipScores = computed(() => plot.value.data?.vip_scores || []);
    const sortedVipScores = computed((): { col: string; vip: number }[] => {
      const selectedVipScores = allVipScores.value[controls.vipComponent - 1];
      if (!selectedVipScores) {
        return [];
      }
      if (controls.sortVip) {
        const copy = [...selectedVipScores];
        copy.sort((a, b) => b.vip - a.vip);
        return copy;
      }
      return selectedVipScores;
    });
    const pcCoords = computed(() => plot.value.data?.scores.x || []);
    const eigenvalues = computed(() => plot.value.data?.scores.sdev || []);
    const rowLabels = computed(() => plot.value.data?.rows || []);
    const groupLabels = computed(() => plot.value.data?.labels || {});
    const columns = computed(() => dataset.value?.column.data || []);
    const groupLevels = computed(() => dataset.value?.groupLevels || []);

    watchEffect(() => {
      const pcX = Number.parseInt(controls.pcXval, 10);
      if (!Number.isNaN(pcX) && pcX <= controls.numComponents) {
        controls.pcX = pcX;
      }
    });
    watchEffect(() => {
      const pcY = Number.parseInt(controls.pcYval, 10);
      if (!Number.isNaN(pcY) && pcY <= controls.numComponents) {
        controls.pcY = pcY;
      }
    });
    watch(() => controls.numComponentsVal, () => {
      const numComponents = Number.parseInt(controls.numComponentsVal, 10);
      if (!Number.isNaN(numComponents)) {
        controls.numComponents = numComponents;
        if (plot.value) {
          plot.value.valid = false;
        }
        changePlotArgs({ num_of_components: controls.numComponents });
      }
    });
    watchEffect(() => {
      const vipComponent = Number.parseInt(controls.vipComponentVal, 10);
      if (!Number.isNaN(vipComponent) && vipComponent <= controls.numComponents) {
        controls.vipComponent = vipComponent;
      }
    });

    function downloadVipScores() {
      const rows: string[] = sortedVipScores.value.map((v) => `${v.col},${v.vip}`);
      downloadCSV(`Metabolite,VIP_Score\n${rows.join('\n')}`, `${dataset.value.name}_PLSDA_VIP_Scores`);
    }

    return {
      plot,
      changePlotArgs,
      controls,
      ready,
      loadings,
      sortedVipScores,
      r2q2Table,
      r2cum,
      q2cum,
      pcCoords,
      eigenvalues,
      rowLabels,
      groupLabels,
      columns,
      groupLevels,
      downloadVipScores,
    };
  },
});
</script>

<template>
  <vis-tile-large
    title="Partial Least Squares Discriminant Analysis"
    :loading="plot.loading"
  >
    <template #controls>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark
        flat
        dense
      >
        <v-toolbar-title>Components</v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mb-3 mx-3"
        flat
      >
        <v-card-actions>
          <v-layout column>
            <v-text-field
              v-model="controls.numComponentsVal"
              class="py-2"
              hide-details
              type="number"
              min="1"
              outline
              :disabled="plot.loading"
              label="Number of Components"
            />
          </v-layout>
        </v-card-actions>
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark
        flat
        dense
      >
        <v-toolbar-title>PC Selector</v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mb-3 mx-3"
        flat
      >
        <v-card-actions>
          <v-layout column>
            <v-text-field
              v-model="controls.pcXval"
              class="py-2"
              hide-details
              type="number"
              label="PC (X Axis)"
              min="1"
              :max="controls.numComponents"
              outline
              :disabled="!controls.showScore && !controls.showLoadings"
            />
            <v-text-field
              v-model="controls.pcYval"
              class="py-2"
              hide-details
              type="number"
              label="PC (Y Axis)"
              min="1"
              :max="controls.numComponents"
              outline
              :disabled="!controls.showScore && !controls.showLoadings"
            />
          </v-layout>
        </v-card-actions>
        <v-card-text class="subheading">
          <table>
            <tbody>
              <tr>
                <th class="px-3" />
                <th class="px-3">
                  R<sup>2</sup>
                </th>
                <th class="px-3">
                  Q<sup>2</sup>
                </th>
              </tr>
              <tr
                v-for="pc in r2q2Table"
                :key="pc.name"
              >
                <td>{{ pc.name }}</td>
                <td>{{ pc.r2 }}</td>
                <td>{{ pc.q2 }}</td>
              </tr>
              <tr>
                <td>
                  <v-divider /> Cum.
                </td>
                <td>
                  <v-divider /> {{ r2cum }}
                </td>
                <td>
                  <v-divider /> {{ q2cum }}
                </td>
              </tr>
            </tbody>
          </table>
        </v-card-text>
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark
        flat
        dense
      >
        <v-toolbar-title class="switch-title">
          Score Plot
          <v-switch
            v-model="controls.showScore"
            class="switch"
            color="white"
            hide-details
          />
        </v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mb-3 mx-3"
        flat
      >
        <v-card-actions>
          <v-layout column>
            <v-switch
              v-model="controls.showEllipses"
              class="ma-0 py-2"
              label="Data ellipses"
              :disabled="!controls.showScore"
              hide-details
            />
          </v-layout>
        </v-card-actions>
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark
        flat
        dense
      >
        <v-toolbar-title class="switch-title">
          Loadings Plot
          <v-switch
            v-model="controls.showLoadings"
            class="switch"
            color="white"
            hide-details
          />
        </v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mb-3 mx-3"
        flat
      >
        <v-card-actions>
          <v-layout column>
            <v-switch
              v-model="controls.showCrosshairs"
              class="ma-0 py-2"
              label="Crosshairs"
              :disabled="!controls.showLoadings"
              hide-details
            />
          </v-layout>
        </v-card-actions>
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark
        flat
        dense
      >
        <v-toolbar-title class="switch-title">
          VIP Plot
          <v-switch
            v-model="controls.showVip"
            class="switch"
            color="white"
            hide-details
          />
        </v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mb-3 mx-3"
        flat
      >
        <v-card-actions>
          <v-layout column>
            <v-text-field
              v-model="controls.vipComponentVal"
              class="py-2"
              hide-details
              type="number"
              label="VIP Plot Component"
              min="1"
              :max="controls.numComponents"
              outline
              :disabled="!controls.showVip"
            />
            <v-switch
              v-model="controls.sortVip"
              class="ma-0 py-2"
              label="Sort VIP plot values"
              :disabled="!controls.showVip"
              hide-details
            />
            <v-btn
              class="my-0 mx-0"
              text
              flat
              @click="downloadVipScores"
            >
              <v-icon> {{ $vuetify.icons.fileDownload }}</v-icon>
              VIP Scores
            </v-btn>
          </v-layout>
        </v-card-actions>
      </v-card>
    </template>
    <layout-grid
      v-if="ready"
      :cell-size="300"
    >
      <score-plot
        v-show="controls.showScore"
        :id="id"
        :pc-x="controls.pcX"
        :pc-y="controls.pcY"
        :show-ellipses="controls.showEllipses"
        :pc-coords="pcCoords"
        :row-labels="rowLabels"
        :columns="columns"
        :eigenvalues="eigenvalues"
        :group-labels="groupLabels"
        :group-levels="groupLevels"
      />
      <loadings-plot
        v-show="controls.showLoadings"
        :id="id"
        :pc-x="controls.pcX"
        :pc-y="controls.pcY"
        :show-crosshairs="controls.showCrosshairs"
        :loadings="loadings"
      />
      <vip-plot
        v-show="controls.showVip"
        :vip-scores="sortedVipScores"
      />
    </layout-grid>
    <div v-else>
      <v-progress-circular
        indeterminate
        size="100"
        width="5"
      />
      <h4 class="display-1 pa-3">
        Loading data...
      </h4>
    </div>
  </vis-tile-large>
</template>

<style lang="scss" scoped>
.switch-title {
  align-items: center;
  display: flex;
  justify-content: space-between;
  overflow: visible;
  width: 100%;
  .switch {
    flex-grow: 0;
    margin-right: -10px;
  }
}
</style>
