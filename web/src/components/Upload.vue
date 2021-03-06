<script>
import { mapState } from 'vuex';
import { sizeFormatter } from '@girder/components/src/utils/mixins';
import Dropzone from '@girder/components/src/components/Presentation/Dropzone.vue';
import FileList from '@girder/components/src/components/Presentation/FileUploadList.vue';
import { UPLOAD_CSV, UPLOAD_EXCEL } from '@/store/actions.type';
import { REMOVE_DATASET } from '@/store/mutations.type';
import SampleBrowser from './SampleBrowser.vue';

function isExcelFile(file) {
  return file.name.match(/\.xlsx$/i);
}

function isCSVFile(file) {
  return file.type === 'text/csv' || file.name.match(/\.csv$/i);
}

function isTextFile(file) {
  return file.type === 'text/plain' || file.name.match(/\.txt$/i);
}

export default {
  components: {
    FileList,
    Dropzone,
    SampleBrowser,
  },
  mixins: [sizeFormatter],
  data() {
    return {
      deleteCount: 0,
      doDelete: () => {},
      pendingFiles: [],
      snackbar: false,
      snackbarContent: '',
      browseSamples: this.$route.meta.try === true,
    };
  },
  computed: {
    ...mapState(['datasets']),
    message() {
      if (this.files.length > 0) {
        return 'Add more files';
      }
      return 'Drag file here or click to select one';
    },
    readyFiles() {
      const { datasets } = this;
      return Object.keys(datasets).map((id) => {
        const d = datasets[id];
        return {
          id: d.id,
          file: {
            name: d.name,
            size: d.size, // TODO: fix when server implements this.
          },
          status: 'done',
          progress: {},
          meta: d,
        };
      });
    },
    files() {
      return this.readyFiles.concat(this.pendingFiles);
    },
    deleteDialog() {
      return this.deleteCount > 0;
    },
  },
  watch: {
    $route(newVal) {
      this.browseSamples = newVal.meta.try === true;
    },
  },
  methods: {
    async onFileChange(targetFiles) {
      if (this.$refs.dropzone && this.$refs.dropzone.$el) {
        const input = this.$refs.dropzone.$el.querySelector('input[type=file]');
        input.value = ''; // reset file input to proper detect same file changes
      }
      // filter to valid types only
      const filteredFiles = targetFiles.filter(
        (f) => isExcelFile(f) || isCSVFile(f) || isTextFile(f),
      );
      const invalidFiles = targetFiles.filter(
        (f) => !(isExcelFile(f) || isCSVFile(f) || isTextFile(f)),
      );

      if (invalidFiles.length > 0) {
        this.snackbarContent = `invalid file extension for: ${invalidFiles.map((d) => d.name).join(', ')}`;
        this.snackbar = true;
      }

      this.pendingFiles = this.pendingFiles.concat([...filteredFiles].map((file) => ({
        file,
        id: `${file.name}-pending`,
        status: 'pending',
        progress: {},
        meta: {},
      })));

      const promises = this.pendingFiles
        .filter((f) => f.status === 'pending')
        .map(async (file) => {
          file.status = 'uploading';
          try {
            await this.$store.dispatch(isExcelFile(file.file) ? UPLOAD_EXCEL : UPLOAD_CSV,
              { file: file.file });
            file.status = 'done';
          } catch (err) {
            file.status = 'error';
            if (err.response) {
              file.meta = err.response.data;
            }
            throw err;
          }
        });
      await Promise.all(promises);
      // filter out done ones
      this.pendingFiles = this.pendingFiles.filter((f) => f.status !== 'done');
    },
    async remove(file) {
      if (file.status === 'done' && file.meta.id) {
        this.$store.commit(REMOVE_DATASET, { dataset_id: file.meta.id });
      } else {
        const i = this.pendingFiles.findIndex((f) => f.name === file.name && f.size === file.size);
        this.pendingFiles.splice(i, 1);
      }
    },
    removeAll() {
      this.readyFiles.concat(this.pendingFiles).forEach((f) => this.remove(f));
    },
  },
};
</script>

<template lang="pug">
v-layout.upload-component(column, fill-height)

  v-snackbar(v-model="snackbar", top, color="error", :timeout="5000")
    | {{snackbarContent}}
    v-btn(dark, flat, @click="snackbar = false") Close

  v-dialog(v-model="deleteDialog", persistent, width="600")
    v-card
      v-card-title.headline
        | Really delete {{ deleteCount }} dataset{{ deleteCount !== 1 ? 's' : ''}}?
      v-card-actions
        v-spacer
        v-btn(@click="doDelete = () => {}; deleteCount = 0;", flat) Cancel
        v-btn(@click="doDelete(); deleteCount = 0", color="error") Delete

  v-layout.grow-overflow(column, fill-height)
    .ma-4
      h3.headline.font-weight-bold.primary--text.text--darken-3 Upload your data (csv, xlsx, or txt)
      p.secondary--text.text--lighten-1 Choose a file from your computer

    .mx-4.mb-4
      v-toolbar.darken-3(color="primary", dark, flat, dense)
        v-toolbar-title All Data Sources
        v-spacer
        v-dialog(v-model="browseSamples", max-width="33vw")
          template(v-slot:activator="{ on }")
            v-btn(flat, small, v-on="on")
              v-icon.pr-1 {{ $vuetify.icons.tablePlus }}
              | try example data source
          v-card
            v-card-title
              h3.headline Examples
            v-card-text.pa-0
              sample-browser(@close="browseSamples = false")
            v-card-actions
              v-spacer
              v-btn(@click="browseSamples = false") Close
        v-btn(flat, small, :to="{ name: 'Merge Data' }", :disabled="files.length < 2")
          v-icon.pr-1 {{ $vuetify.icons.tablePlus }}
          | merge data sources
        v-btn(flat, small, @click="deleteCount = files.length; doDelete = removeAll")
          v-icon.pr-1 {{ $vuetify.icons.clearAll }}
          | clear all
      v-list.upload-list
        template(v-for="(file, idx) in files")
          v-list-tile.pa-2(:key="file.id")
            v-list-tile-action
              v-btn(:disabled="file.status === 'uploading'",
                  icon, @click="doDelete = () => { remove(file); }; deleteCount = 1;")
                v-icon {{ $vuetify.icons.close }}
            v-list-tile-content.shrink
              v-list-tile-title(v-text="`${file.file.name} `")
              v-list-tile-sub-title
                | {{file.file.size != null ? formatSize(file.file.size) : '?'}}
            v-list-tile-content.px-2.shrink(v-if="file.status === 'error'")
              v-chip.largetext(small, color="error", text-color="white")
                v-avatar
                  v-icon {{ $vuetify.icons.warningCircle }}
                span(v-if="file.meta.name") {{ file.meta.name[0] }}
                span(v-else-if="file.meta.table") {{ file.meta.table[0] }}
                span(v-else) Fatal Error

            v-list-tile-content.px-2.shrink(v-if="file.status === 'done' && file.meta.ready")
              v-layout(row, align-center)
                v-chip.largetext(v-if="file.meta.validation.length === 0",
                    small, color="success", text-color="white")
                  v-avatar
                    v-icon {{ $vuetify.icons.checkCircle }}
                  span Dataset ready for analysis.
                v-chip.largetext(v-else, small, color="warning", text-color="")
                  v-avatar
                    v-icon {{ $vuetify.icons.warningCircle }}
                  span Dataset processed with {{ file.meta.validation.length }} validation failures
                v-btn(small, outline, color="primary", round,
                    :to="{ name: 'Clean Up Table', params: { id: file.meta.id } }")
                  v-icon.pr-1 {{ $vuetify.icons.eye }}
                  |  View Data
            v-list-tile-content.px-2.shrink(
                v-if="file.status === 'uploading' || file.meta.ready === false")
              v-progress-circular(size="24", color="primary", indeterminate)
          v-divider(v-if="idx + 1 < files.length", :key="idx")
    dropzone.filezone.mx-4.mb-4(ref="dropzone", :multiple="true", :message="message",
        @change="onFileChange", accept=".csv,.xlsx,.txt")
</template>

<style lang="scss", scoped>
.tag-selection {
  width: 200px;
}

.filezone {
  min-width: 300px;
  min-height: 250px;
}

.largetext {
  font-size: 15px;
}
</style>

<style lang="scss">
.upload-component {
  .v-btn--small {
    height: 24px;
  }
}
</style>
