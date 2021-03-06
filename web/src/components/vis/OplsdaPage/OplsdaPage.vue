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
    const { dataset, plot, changePlotArgs } = usePlotData(toRef(props, 'id'), 'oplsda');
    const controls = reactive({
      pcYval: '1',
      numComponentsVal: '2',
      pcY: 2,
      numComponents: 2,
      group1: dataset.value?.groupLevels[0]?.name || null,
      group2: dataset.value?.groupLevels[1]?.name || null,
      showEllipses: true,
      showCrosshairs: true,
      showCutoffs: true,
      showScore: true,
      showLoadings: true,
      showVip: true,
      sortVip: false,
    });

    const ready = computed(() => {
      const pcaReady = store.getters.ready(props.id, 'plsda_scores');
      const loadingsReady = store.getters.ready(props.id, 'plsda_loadings');
      return pcaReady && loadingsReady;
    });
    const r2: ComputedRef<number[]> = computed(() => plot.value.data?.r2 || []);
    const q2: ComputedRef<number[]> = computed(() => plot.value.data?.q2 || []);
    const r2q2Table = computed(() => r2.value.map((r2Val, i) => {
      if (i === 0) {
        return { name: 'P', r2: r2Val.toFixed(3), q2: q2.value[i].toFixed(3) };
      }
      return {
        name: `O${i}`, r2: r2Val.toFixed(3), q2: q2.value[i].toFixed(3), index: i,
      };
    }));
    const loadings = computed(() => plot.value.data?.loadings || []);
    const vipScores = computed(() => plot.value.data?.vip_scores || []);
    const sortedVipScores = computed((): { col: string; vip: number }[] => {
      if (controls.sortVip) {
        const copy = [...vipScores.value];
        copy.sort((a, b) => b.vip - a.vip);
        return copy;
      }
      return vipScores.value;
    });
    const pcCoords = computed(() => plot.value.data?.scores.x || []);
    const eigenvalues = computed(() => plot.value.data?.scores.sdev || []);
    const rowLabels = computed(() => plot.value.data?.rows || []);
    const groupLabels = computed(() => plot.value.data?.labels || {});
    const columns = computed(() => dataset.value?.column?.data || []);
    const groupLevels = computed(() => dataset.value?.groupLevels || []);
    const groupNames = computed(() => groupLevels.value.map(
      (level: { name: string }) => level.name,
    ));

    watchEffect(() => {
      const pcY = Number.parseInt(controls.pcYval, 10);
      if (!Number.isNaN(pcY) && pcY <= controls.numComponents) {
        // The first of the 6 components is always pcX
        // We want to express pcY as an integer in [1..5], but use it as a number in [2..6]
        controls.pcY = pcY + 1;
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

    // These two watchers prevent the same group from being selected twice.
    watch(() => controls.group1, (newGroup, oldGroup) => {
      changePlotArgs({ group1: newGroup });
      // When setting the same group twice, switch them instead
      if (controls.group2 === newGroup) {
        controls.group2 = oldGroup;
        changePlotArgs({ group2: oldGroup });
      }
      // only force a refresh if both groups are set
      if (plot.value && controls.group1 && controls.group2) {
        plot.value.valid = false;
      }
    });
    watch(() => controls.group2, (newGroup, oldGroup) => {
      changePlotArgs({ group2: newGroup });
      // When setting the same group twice, switch them instead
      if (controls.group1 === newGroup) {
        controls.group1 = oldGroup;
        changePlotArgs({ group1: oldGroup });
      }
      // only force a refresh if both groups are set
      if (plot.value && controls.group1 && controls.group2) {
        plot.value.valid = false;
      }
    });

    function downloadVipScores() {
      const rows: string[] = sortedVipScores.value.map((v) => `${v.col},${v.vip}`);
      downloadCSV(`Metabolite,VIP_Score\n${rows.join('\n')}`, `${dataset.value.name}_OPLSDA_VIP_Scores`);
    }

    return {
      plot,
      changePlotArgs,
      controls,
      ready,
      r2,
      r2q2Table,
      loadings,
      sortedVipScores,
      pcCoords,
      eigenvalues,
      rowLabels,
      groupLabels,
      columns,
      groupLevels,
      groupNames,
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
              v-model="controls.pcYval"
              class="py-2"
              hide-details
              type="number"
              label="Orthogonal (Y Axis)"
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
                :class="(pc.index===controls.pcY-1)? 'font-weight-bold':''"
                @click="if (pc.index) controls.pcYval=pc.index"
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
                  <v-divider /> {{ plot.data ? plot.data.r2cum.toFixed(3) : '0' }}
                </td>
                <td>
                  <v-divider /> {{ plot.data ? plot.data.q2cum.toFixed(3) : '0' }}
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
        :card="false"
      >
        <v-toolbar-title>Group 1</v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mx-3 px-2"
        flat="flat"
      >
        <v-select
          v-model="controls.group1"
          class="py-2"
          hide-details="hide-details"
          :items="groupNames"
        />
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark="dark"
        flat="flat"
        dense="dense"
        :card="false"
      >
        <v-toolbar-title>Group 2</v-toolbar-title>
      </v-toolbar>
      <v-card
        class="mx-3 px-2"
        flat="flat"
      >
        <v-select
          v-model="controls.group2"
          class="py-2"
          hide-details="hide-details"
          :items="groupNames"
        />
      </v-card>
      <v-toolbar
        class="darken-3"
        color="primary"
        dark="dark"
        flat="flat"
        dense="dense"
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
        :pc-x="1"
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
        :pc-x="1"
        :pc-y="controls.pcY"
        :show-crosshairs="controls.showCrosshairs"
        :loadings="loadings"
      />
      <vip-plot
        v-show="controls.showVip"
        :vip-scores="sortedVipScores"
        :sort-vip="controls.sortVip"
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
