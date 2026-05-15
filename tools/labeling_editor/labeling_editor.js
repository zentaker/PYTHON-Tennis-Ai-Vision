const EDITOR_VERSION = "0.3.0";

const state = {
  videoName: "",
  objectUrl: "",
  labels: [],
  windows: [],
  selectedKind: "",
  selectedId: "",
  thumbnails: [],
  thumbnailStatus: "idle",
  zoom: 1,
  fitPixelsPerSecond: 1,
  pixelsPerSecond: 1,
  windowStart: null,
  windowEnd: null,
  isScrubbing: false,
  rangeDrag: null,
  lastAction: "Ready",
  lastError: null,
};

const MIN_VISIBLE_RANGE_WIDTH = 44;

const labelColors = {
  pre_bounce: "#5db7ff",
  bounce_contact: "#47e56f",
  post_bounce: "#46d8d0",
  hit: "#ff9f40",
  no_event: "#9e9e9e",
  uncertain: "#b879ff",
  bounce_window: "rgba(71, 229, 111, 0.28)",
  hit_window: "rgba(255, 159, 64, 0.28)",
  uncertain_window: "rgba(184, 121, 255, 0.28)",
  bounce: "#47e56f",
  no_event_range: "rgba(158, 158, 158, 0.24)",
};

const video = document.getElementById("video");
const videoInput = document.getElementById("videoInput");
const labelInput = document.getElementById("labelInput");
const fpsInput = document.getElementById("fpsInput");
const confidenceInput = document.getElementById("confidenceInput");
const notesInput = document.getElementById("notesInput");
const currentTimeText = document.getElementById("currentTimeText");
const durationText = document.getElementById("durationText");
const frameText = document.getElementById("frameText");
const videoNameText = document.getElementById("videoNameText");
const labelList = document.getElementById("labelList");
const windowList = document.getElementById("windowList");
const playPauseButton = document.getElementById("playPauseButton");
const statusText = document.getElementById("statusText");
const rangeDebugText = document.getElementById("rangeDebugText");
const smokeTestButton = document.getElementById("smokeTestButton");
const semanticWarningText = document.getElementById("semanticWarningText");
const timelineViewport = document.getElementById("timelineViewport");
const timelineContent = document.getElementById("timelineContent");
const rulerLane = document.getElementById("rulerLane");
const windowLane = document.getElementById("windowLane");
const markerLane = document.getElementById("markerLane");
const thumbnailStrip = document.getElementById("thumbnailStrip");
const playhead = document.getElementById("playhead");
const zoomText = document.getElementById("zoomText");
const visibleRangeText = document.getElementById("visibleRangeText");
const ppsText = document.getElementById("ppsText");
const windowSelectionText = document.getElementById("windowSelectionText");

function fps() {
  const value = Number(fpsInput.value || 60);
  return Number.isFinite(value) && value > 0 ? value : 60;
}

function rawFpsValue() {
  return Number(fpsInput.value || 0);
}

function duration() {
  const value = Number(video.duration || 0);
  return Number.isFinite(value) ? value : 0;
}

function clamp(value, min, max) {
  if (max < min) {
    return min;
  }
  return Math.max(min, Math.min(max, value));
}

function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds || 0));
  const minutes = Math.floor(safe / 60);
  const remainder = safe - minutes * 60;
  return `${String(minutes).padStart(2, "0")}:${remainder.toFixed(3).padStart(6, "0")}`;
}

function frameEstimate(seconds) {
  return Math.round(Number(seconds || 0) * fps());
}

function newId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

function setStatus(message) {
  statusText.textContent = message;
  window.clearTimeout(setStatus.timeoutId);
  setStatus.timeoutId = window.setTimeout(() => {
    statusText.textContent = state.thumbnailStatus === "generating" ? "Generating thumbnails..." : "Ready";
  }, 2600);
}

function setLastAction(message, error = null) {
  state.lastAction = message;
  state.lastError = error;
  renderDebugStatus();
}

function renderDebugStatus() {
  if (!rangeDebugText) {
    return;
  }
  const suffix = state.lastError ? ` | Last error: ${state.lastError}` : "";
  rangeDebugText.textContent = `Range count: ${state.windows.length} | Last action: ${state.lastAction}${suffix}`;
}

function secondsToX(seconds) {
  return Number(seconds || 0) * state.pixelsPerSecond;
}

function xToSeconds(x) {
  return clamp(Number(x || 0) / Math.max(state.pixelsPerSecond, 0.001), 0, duration());
}

function currentLabelPayload(labelType) {
  const time = Number(video.currentTime || 0);
  return {
    label_id: newId("label"),
    label_type: labelType,
    time_seconds: Number(time.toFixed(3)),
    frame_estimate: frameEstimate(time),
    fps_used: fps(),
    confidence: confidenceInput.value || "high",
    notes: notesInput.value || "",
  };
}

function addLabel(labelType) {
  if (!video.src) {
    return;
  }
  const label = currentLabelPayload(labelType);
  state.labels.push(label);
  state.selectedKind = "label";
  state.selectedId = label.label_id;
  setStatus(`Added point label: ${labelType} at ${formatTime(label.time_seconds)} / frame ${label.frame_estimate}.`);
  render();
}

function deleteSelected() {
  if (state.selectedKind === "label") {
    state.labels = state.labels.filter((label) => label.label_id !== state.selectedId);
  } else if (state.selectedKind === "range" || state.selectedKind === "window") {
    state.windows = state.windows.filter((item) => rangeId(item) !== state.selectedId);
  }
  state.selectedKind = "";
  state.selectedId = "";
  render();
}

function seekTime(time) {
  if (!video.src) {
    return;
  }
  video.currentTime = clamp(time, 0, duration());
  updatePlayhead();
}

function selectLabel(label) {
  state.selectedKind = "label";
  state.selectedId = label.label_id;
  seekTime(Number(label.time_seconds || 0));
  render();
}

function selectWindow(windowLabel) {
  state.selectedKind = "range";
  state.selectedId = rangeId(windowLabel);
  seekTime(Number(windowLabel.center_time_seconds || 0));
  render();
}

function updateLabel(labelId, patch) {
  state.labels = state.labels.map((label) => (label.label_id === labelId ? { ...label, ...patch } : label));
  renderTimeline();
}

function updateWindow(windowId, patch) {
  state.windows = state.windows.map((item) => (rangeId(item) === windowId ? { ...item, ...patch } : item));
  renderTimeline();
}

function sortedLabels() {
  return [...state.labels].sort((a, b) => Number(a.time_seconds) - Number(b.time_seconds));
}

function sortedWindows() {
  return [...state.windows].sort((a, b) => Number(a.start_time_seconds) - Number(b.start_time_seconds));
}

function rangeId(item) {
  return String(item.range_id || item.window_id || "");
}

function normalizeRangeType(labelType) {
  return String(labelType || "uncertain").replace("_window", "");
}

function contactEstimateTime(item) {
  if (item.contact_estimate_time_seconds !== undefined && item.contact_estimate_time_seconds !== "") {
    return Number(item.contact_estimate_time_seconds);
  }
  return Number(item.center_time_seconds || 0);
}

function duplicateBounceContactWarnings() {
  const contacts = sortedLabels().filter((label) => label.label_type === "bounce_contact");
  const thresholdSeconds = Math.max(2 / fps(), 0.05);
  const warnings = [];
  for (let index = 1; index < contacts.length; index += 1) {
    const previous = contacts[index - 1];
    const current = contacts[index];
    const delta = Math.abs(Number(current.time_seconds) - Number(previous.time_seconds));
    if (delta <= thresholdSeconds) {
      warnings.push(
        `Multiple bounce_contact labels detected in a very short interval. Consider using one bounce_window plus one bounce_contact. Frames ${frameEstimate(previous.time_seconds)} and ${frameEstimate(current.time_seconds)} are ${delta.toFixed(3)}s apart.`,
      );
    }
  }
  return warnings;
}

function renderSemanticWarnings() {
  const warnings = duplicateBounceContactWarnings();
  if (!warnings.length) {
    semanticWarningText.hidden = true;
    semanticWarningText.textContent = "";
    return;
  }
  semanticWarningText.hidden = false;
  semanticWarningText.textContent = warnings[0];
}

function calculateTimelineMetrics() {
  const clipDuration = duration();
  const viewportWidth = timelineViewport.clientWidth || 900;
  state.fitPixelsPerSecond = clipDuration > 0 ? viewportWidth / clipDuration : 1;
  state.pixelsPerSecond = Math.max(24, state.fitPixelsPerSecond * state.zoom);
  if (clipDuration > 0 && state.zoom <= 1.001) {
    state.pixelsPerSecond = state.fitPixelsPerSecond;
  }
  const width = Math.max(viewportWidth, clipDuration * state.pixelsPerSecond);
  timelineContent.style.width = `${width}px`;
}

function chooseTickInterval() {
  const pps = state.pixelsPerSecond;
  const candidates = [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60];
  return candidates.find((step) => step * pps >= 80) || 120;
}

function renderRuler() {
  rulerLane.innerHTML = "";
  const clipDuration = duration();
  if (!clipDuration) {
    return;
  }
  const interval = chooseTickInterval();
  for (let time = 0; time <= clipDuration + 0.0001; time += interval) {
    const tick = document.createElement("div");
    tick.className = "ruler-tick";
    tick.style.left = `${secondsToX(time)}px`;
    const label = document.createElement("span");
    label.textContent = state.pixelsPerSecond > 500 ? `${formatTime(time)} / f${frameEstimate(time)}` : formatTime(time);
    tick.append(label);
    rulerLane.append(tick);
  }
}

function renderThumbnails() {
  thumbnailStrip.innerHTML = "";
  const clipDuration = duration();
  if (!clipDuration) {
    thumbnailStrip.textContent = "Load a video to generate thumbnails.";
    return;
  }
  if (state.thumbnailStatus === "generating") {
    thumbnailStrip.textContent = "Generating thumbnails...";
    return;
  }
  if (!state.thumbnails.length) {
    thumbnailStrip.textContent = "No thumbnails generated yet.";
    return;
  }
  const slotDuration = clipDuration / state.thumbnails.length;
  state.thumbnails.forEach((thumb, index) => {
    const image = document.createElement("img");
    image.src = thumb.url;
    image.alt = `thumbnail ${formatTime(thumb.time)}`;
    image.className = "timeline-thumbnail";
    image.style.left = `${secondsToX(thumb.time)}px`;
    image.style.width = `${Math.max(42, slotDuration * state.pixelsPerSecond)}px`;
    image.addEventListener("click", () => seekTime(thumb.time));
    image.dataset.index = String(index);
    thumbnailStrip.append(image);
  });
}

function renderMarkers() {
  markerLane.innerHTML = "";
  sortedLabels().forEach((label) => {
    const marker = document.createElement("button");
    marker.type = "button";
    marker.className = `timeline-marker ${label.label_type}`;
    if (state.selectedKind === "label" && state.selectedId === label.label_id) {
      marker.classList.add("selected");
    }
    marker.style.left = `${secondsToX(label.time_seconds)}px`;
    marker.title = `${label.label_type} ${formatTime(label.time_seconds)}`;
    marker.addEventListener("click", (event) => {
      event.stopPropagation();
      selectLabel(label);
    });
    markerLane.append(marker);
  });
}

function renderWindows() {
  windowLane.innerHTML = "";
  console.debug("renderRanges called", { rangeCount: state.windows.length });
  sortedWindows().forEach((item) => {
    const id = rangeId(item);
    const type = normalizeRangeType(item.label_type);
    const range = document.createElement("div");
    range.className = `timeline-window event-range ${type}_range`;
    if (state.selectedKind === "range" && state.selectedId === id) {
      range.classList.add("selected");
    }
    const start = Number(item.start_time_seconds || 0);
    const end = Number(item.end_time_seconds || start);
    const actualWidth = secondsToX(end) - secondsToX(start);
    const visibleWidth = Math.max(MIN_VISIBLE_RANGE_WIDTH, actualWidth);
    range.style.left = `${secondsToX(start)}px`;
    range.style.width = `${visibleWidth}px`;
    console.debug("range rendered", { id, type, start, end, visibleWidth });
    range.title = `${type} ${formatTime(start)} - ${formatTime(end)}`;
    const leftHandle = document.createElement("span");
    leftHandle.className = "range-handle left";
    const label = document.createElement("span");
    label.className = "range-label";
    label.textContent = visibleWidth > 48 ? type : type.slice(0, 1).toUpperCase();
    const contact = document.createElement("span");
    contact.className = "range-contact-estimate";
    const contactTime = contactEstimateTime(item);
    contact.style.left = `${Math.max(2, Math.min(visibleWidth - 2, secondsToX(contactTime) - secondsToX(start)))}px`;
    const rightHandle = document.createElement("span");
    rightHandle.className = "range-handle right";
    range.append(leftHandle, label, contact, rightHandle);
    range.addEventListener("click", (event) => {
      event.stopPropagation();
      selectWindow(item);
    });
    range.addEventListener("pointerdown", (event) => beginRangeDrag(event, item, "move"));
    leftHandle.addEventListener("pointerdown", (event) => beginRangeDrag(event, item, "resize-left"));
    rightHandle.addEventListener("pointerdown", (event) => beginRangeDrag(event, item, "resize-right"));
    windowLane.append(range);
  });
}

function updatePlayhead() {
  playhead.style.left = `${secondsToX(video.currentTime)}px`;
  renderTime();
}

function renderZoomStatus() {
  const start = xToSeconds(timelineViewport.scrollLeft);
  const end = xToSeconds(timelineViewport.scrollLeft + timelineViewport.clientWidth);
  zoomText.textContent = `Timeline zoom: ${state.zoom.toFixed(1)}x`;
  visibleRangeText.textContent = `Visible: ${formatTime(start)} - ${formatTime(end)}`;
  ppsText.textContent = `${state.pixelsPerSecond.toFixed(1)} px/s`;
}

function renderWindowSelection() {
  if (state.windowStart === null && state.windowEnd === null) {
    windowSelectionText.textContent = "Window: none";
    return;
  }
  const start = state.windowStart === null ? video.currentTime : state.windowStart;
  const end = state.windowEnd === null ? video.currentTime : state.windowEnd;
  windowSelectionText.textContent = `Window: ${formatTime(Math.min(start, end))} - ${formatTime(Math.max(start, end))}`;
}

function renderTimeline() {
  calculateTimelineMetrics();
  renderRuler();
  renderThumbnails();
  renderWindows();
  renderMarkers();
  updatePlayhead();
  renderZoomStatus();
  renderWindowSelection();
}

function ensureRangeVisible(range) {
  const center = Number(range.center_time_seconds || range.contact_estimate_time_seconds || 0);
  const centerX = secondsToX(center);
  const padding = Math.min(180, Math.max(40, timelineViewport.clientWidth * 0.2));
  if (centerX < timelineViewport.scrollLeft + padding || centerX > timelineViewport.scrollLeft + timelineViewport.clientWidth - padding) {
    timelineViewport.scrollLeft = Math.max(0, centerX - timelineViewport.clientWidth / 2);
  }
  renderZoomStatus();
}

function renderTime() {
  const clipDuration = duration();
  currentTimeText.textContent = formatTime(video.currentTime);
  durationText.textContent = formatTime(clipDuration);
  frameText.textContent = `frame est. ${frameEstimate(video.currentTime)}`;
  playPauseButton.textContent = video.paused ? "Play" : "Pause";
}

function renderList() {
  labelList.innerHTML = "";
  sortedLabels().forEach((label) => {
    const item = document.createElement("li");
    item.className = `label-item ${label.label_type}`;
    if (state.selectedKind === "label" && label.label_id === state.selectedId) {
      item.classList.add("selected");
    }
    item.style.borderLeftColor = labelColors[label.label_type] || "#aaa";
    const header = document.createElement("header");
    const title = document.createElement("strong");
    title.textContent = `POINT LABEL: ${label.label_type}`;
    const time = document.createElement("small");
    time.textContent = `${formatTime(label.time_seconds)} | frame ${frameEstimate(label.time_seconds)}`;
    header.append(title, time);
    const confidence = createConfidenceSelect(label.confidence, (value) => updateLabel(label.label_id, { confidence: value }));
    const notes = createNotesInput(label.notes, (value) => updateLabel(label.label_id, { notes: value }));
    const actions = createItemActions(() => selectLabel(label), () => {
      state.selectedKind = "label";
      state.selectedId = label.label_id;
      deleteSelected();
    });
    item.addEventListener("click", () => selectLabel(label));
    item.append(header, confidence, notes, actions);
    labelList.append(item);
  });
}

function renderWindowList() {
  windowList.innerHTML = "";
  sortedWindows().forEach((item) => {
    const id = rangeId(item);
    const type = normalizeRangeType(item.label_type);
    const row = document.createElement("li");
    row.className = `label-item ${type}_range`;
    if (state.selectedKind === "range" && id === state.selectedId) {
      row.classList.add("selected");
    }
    row.style.borderLeftColor = labelColors[type] || "#aaa";
    const header = document.createElement("header");
    const title = document.createElement("strong");
    title.textContent = `EVENT RANGE: ${type}`;
    const time = document.createElement("small");
    time.textContent = `start ${formatTime(item.start_time_seconds)} | end ${formatTime(item.end_time_seconds)} | contact est. ${formatTime(contactEstimateTime(item))} | frames ${frameEstimate(item.start_time_seconds)}-${frameEstimate(item.end_time_seconds)}`;
    header.append(title, time);
    const confidence = createConfidenceSelect(item.confidence, (value) => updateWindow(id, { confidence: value }));
    const notes = createNotesInput(item.notes, (value) => updateWindow(id, { notes: value }));
    const actions = createItemActions(() => selectWindow(item), () => {
      state.selectedKind = "range";
      state.selectedId = id;
      deleteSelected();
    });
    row.addEventListener("click", () => selectWindow(item));
    row.append(header, confidence, notes, actions);
    windowList.append(row);
  });
}

function createConfidenceSelect(value, onChange) {
  const confidence = document.createElement("select");
  ["high", "medium", "low"].forEach((item) => {
    const option = document.createElement("option");
    option.value = item;
    option.textContent = item;
    option.selected = item === value;
    confidence.append(option);
  });
  confidence.addEventListener("click", (event) => event.stopPropagation());
  confidence.addEventListener("change", () => onChange(confidence.value));
  return confidence;
}

function createNotesInput(value, onChange) {
  const notes = document.createElement("input");
  notes.value = value || "";
  notes.placeholder = "notes";
  notes.addEventListener("click", (event) => event.stopPropagation());
  notes.addEventListener("change", () => onChange(notes.value));
  return notes;
}

function createItemActions(onSeek, onDelete) {
  const actions = document.createElement("div");
  actions.className = "item-actions";
  const seekButton = document.createElement("button");
  seekButton.type = "button";
  seekButton.textContent = "Seek";
  seekButton.addEventListener("click", (event) => {
    event.stopPropagation();
    onSeek();
  });
  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.textContent = "Delete";
  deleteButton.addEventListener("click", (event) => {
    event.stopPropagation();
    onDelete();
  });
  actions.append(seekButton, deleteButton);
  return actions;
}

function render() {
  videoNameText.textContent = state.videoName || "No video loaded";
  renderTime();
  renderTimeline();
  renderList();
  renderWindowList();
  renderSemanticWarnings();
  renderDebugStatus();
}

function togglePlayback() {
  if (!video.src) {
    return;
  }
  if (video.paused) {
    video.play();
  } else {
    video.pause();
  }
}

function step(seconds) {
  if (!video.src) {
    return;
  }
  seekTime(Number(video.currentTime || 0) + seconds);
}

function setZoom(nextZoom, anchorClientX = null) {
  const clipDuration = duration();
  if (!clipDuration) {
    return;
  }
  const rect = timelineViewport.getBoundingClientRect();
  const anchorX = anchorClientX === null ? rect.width / 2 : anchorClientX - rect.left;
  const anchorTime = xToSeconds(timelineViewport.scrollLeft + anchorX);
  state.zoom = clamp(nextZoom, 1, 32);
  calculateTimelineMetrics();
  timelineViewport.scrollLeft = Math.max(0, secondsToX(anchorTime) - anchorX);
  renderTimeline();
}

function fitClip() {
  state.zoom = 1;
  timelineViewport.scrollLeft = 0;
  renderTimeline();
}

function timelineTimeFromEvent(event) {
  const rect = timelineViewport.getBoundingClientRect();
  const x = timelineViewport.scrollLeft + event.clientX - rect.left;
  return xToSeconds(x);
}

function beginScrub(event) {
  if (event.target.closest("button")) {
    return;
  }
  state.isScrubbing = true;
  seekTime(timelineTimeFromEvent(event));
  timelineViewport.setPointerCapture(event.pointerId);
}

function scrubMove(event) {
  if (!state.isScrubbing) {
    return;
  }
  seekTime(timelineTimeFromEvent(event));
}

function endScrub(event) {
  state.isScrubbing = false;
  try {
    timelineViewport.releasePointerCapture(event.pointerId);
  } catch (_error) {
    // Pointer capture can already be released by the browser.
  }
}

function beginRangeDrag(event, item, mode) {
  event.preventDefault();
  event.stopPropagation();
  const id = rangeId(item);
  state.selectedKind = "range";
  state.selectedId = id;
  state.rangeDrag = {
    id,
    mode,
    clientX: event.clientX,
    start: Number(item.start_time_seconds || 0),
    end: Number(item.end_time_seconds || 0),
  };
  render();
}

function updateDraggedRange(event) {
  if (!state.rangeDrag) {
    return;
  }
  event.preventDefault();
  const drag = state.rangeDrag;
  const deltaSeconds = (event.clientX - drag.clientX) / Math.max(state.pixelsPerSecond, 0.001);
  const minDuration = Math.max(1 / fps(), 0.01);
  const clipDuration = duration();
  state.windows = state.windows.map((item) => {
    if (rangeId(item) !== drag.id) {
      return item;
    }
    let start = drag.start;
    let end = drag.end;
    if (drag.mode === "move") {
      const length = Math.max(minDuration, drag.end - drag.start);
      start = clamp(drag.start + deltaSeconds, 0, Math.max(0, clipDuration - length));
      end = start + length;
    } else if (drag.mode === "resize-left") {
      start = clamp(drag.start + deltaSeconds, 0, drag.end - minDuration);
      end = drag.end;
    } else if (drag.mode === "resize-right") {
      start = drag.start;
      end = clamp(drag.end + deltaSeconds, drag.start + minDuration, clipDuration);
    }
    const center = (start + end) / 2;
    return {
      ...item,
      start_time_seconds: Number(start.toFixed(3)),
      end_time_seconds: Number(end.toFixed(3)),
      center_time_seconds: Number(center.toFixed(3)),
      contact_estimate_time_seconds: Number(center.toFixed(3)),
      start_frame_estimate: frameEstimate(start),
      end_frame_estimate: frameEstimate(end),
      center_frame_estimate: frameEstimate(center),
      contact_frame_estimate: frameEstimate(center),
    };
  });
  renderTimeline();
  renderWindowList();
}

function endRangeDrag() {
  if (state.rangeDrag) {
    setStatus("Updated event range.");
  }
  state.rangeDrag = null;
}

async function waitForEvent(element, eventName) {
  return new Promise((resolve) => {
    const handler = () => {
      element.removeEventListener(eventName, handler);
      resolve();
    };
    element.addEventListener(eventName, handler);
  });
}

async function generateThumbnails() {
  if (!state.objectUrl || !duration()) {
    return;
  }
  state.thumbnailStatus = "generating";
  setStatus("Generating thumbnails...");
  renderTimeline();
  const thumbVideo = document.createElement("video");
  thumbVideo.muted = true;
  thumbVideo.preload = "auto";
  thumbVideo.src = state.objectUrl;
  await waitForEvent(thumbVideo, "loadedmetadata");
  if (thumbVideo.readyState < 2) {
    await waitForEvent(thumbVideo, "loadeddata");
  }
  const clipDuration = Number(thumbVideo.duration || duration());
  const count = clamp(Math.ceil(clipDuration * 2), 24, 140);
  const canvas = document.createElement("canvas");
  canvas.width = 160;
  canvas.height = 90;
  const context = canvas.getContext("2d");
  const thumbnails = [];
  for (let index = 0; index < count; index += 1) {
    const time = clipDuration <= 0 ? 0 : (index / Math.max(1, count - 1)) * clipDuration;
    const sampleTime = Math.min(Math.max(0, clipDuration - 0.001), time);
    if (Math.abs(Number(thumbVideo.currentTime || 0) - sampleTime) > 0.001) {
      thumbVideo.currentTime = sampleTime;
      await waitForEvent(thumbVideo, "seeked");
    }
    context.fillStyle = "#000";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(thumbVideo, 0, 0, canvas.width, canvas.height);
    thumbnails.push({ time: sampleTime, url: canvas.toDataURL("image/jpeg", 0.68) });
    if (index % 8 === 0) {
      state.thumbnails = thumbnails.slice();
      renderTimeline();
      await new Promise((resolve) => window.requestAnimationFrame(resolve));
    }
  }
  state.thumbnails = thumbnails;
  state.thumbnailStatus = "ready";
  setStatus(`Generated ${thumbnails.length} thumbnails.`);
  renderTimeline();
}

function setWindowStart() {
  state.windowStart = Number(video.currentTime || 0);
  renderWindowSelection();
  setStatus(`Window start set at ${formatTime(state.windowStart)}.`);
}

function setWindowEnd() {
  state.windowEnd = Number(video.currentTime || 0);
  renderWindowSelection();
  setStatus(`Window end set at ${formatTime(state.windowEnd)}.`);
}

function clearWindowSelection() {
  state.windowStart = null;
  state.windowEnd = null;
  renderWindowSelection();
  setStatus("Window selection cleared.");
}

function buildRange(labelType, start, end) {
  const cleanType = normalizeRangeType(labelType);
  const clipDuration = duration();
  const minDuration = Math.max(1 / fps(), 0.01);
  const rawStart = Math.min(start, end);
  const rawEnd = Math.max(start, end);
  let safeStart = clamp(rawStart, 0, Math.max(0, clipDuration - minDuration));
  let safeEnd = clamp(rawEnd, safeStart + minDuration, clipDuration);
  if (safeEnd > clipDuration) {
    safeEnd = clipDuration;
    safeStart = clamp(safeEnd - minDuration, 0, safeEnd);
  }
  const center = (safeStart + safeEnd) / 2;
  const id = newId("range");
  return {
    range_id: id,
    window_id: id,
    label_type: cleanType,
    start_time_seconds: Number(safeStart.toFixed(3)),
    end_time_seconds: Number(safeEnd.toFixed(3)),
    center_time_seconds: Number(center.toFixed(3)),
    contact_estimate_time_seconds: Number(center.toFixed(3)),
    start_frame_estimate: frameEstimate(safeStart),
    end_frame_estimate: frameEstimate(safeEnd),
    center_frame_estimate: frameEstimate(center),
    contact_frame_estimate: frameEstimate(center),
    fps_used: fps(),
    confidence: confidenceInput.value || "high",
    notes: notesInput.value || "",
  };
}

function addEventRange(labelType) {
  console.debug("addRange called", { labelType });
  if (!video.src || !duration()) {
    setStatus("Load a video before adding ranges.");
    setLastAction("Range not added", "Load a video before adding ranges.");
    console.debug("range creation blocked: no video loaded");
    return;
  }
  if (!Number.isFinite(rawFpsValue()) || rawFpsValue() <= 0) {
    fpsInput.value = "60";
    setStatus("Invalid FPS found. Defaulted to 60 FPS.");
    console.debug("range creation defaulted invalid fps", { fps: fpsInput.value });
  }
  const defaultDuration = Math.max(3 / fps(), 0.05);
  const current = Number(video.currentTime || 0);
  const range = buildRange(labelType, current - defaultDuration / 2, current + defaultDuration / 2);
  console.debug("range created", {
    labelType: range.label_type,
    start: range.start_time_seconds,
    end: range.end_time_seconds,
  });
  state.windows.push(range);
  console.debug("range count after push", { rangeCount: state.windows.length });
  state.selectedKind = "range";
  state.selectedId = rangeId(range);
  const action = `Added ${normalizeRangeType(labelType)} range`;
  setStatus(`${action} at ${formatTime(range.center_time_seconds)}.`);
  setLastAction(action, null);
  render();
  ensureRangeVisible(range);
}

function saveWindow(labelType) {
  if (state.windowStart === null || state.windowEnd === null) {
    setStatus("Set window start and end first.");
    return;
  }
  const start = Math.min(state.windowStart, state.windowEnd);
  const end = Math.max(state.windowStart, state.windowEnd);
  const windowLabel = buildRange(labelType, start, end);
  state.windows.push(windowLabel);
  state.selectedKind = "range";
  state.selectedId = rangeId(windowLabel);
  clearWindowSelection();
  setStatus(`Added range: ${normalizeRangeType(labelType)} ${formatTime(start)} - ${formatTime(end)}.`);
  render();
}

function exportPayload() {
  const currentFps = fps();
  const eventRanges = sortedWindows().map((item) => {
    const type = normalizeRangeType(item.label_type);
    const start = Number(item.start_time_seconds || 0);
    const end = Number(item.end_time_seconds || start);
    const center = (start + end) / 2;
    const contact = Number(contactEstimateTime(item) || center);
    return {
      range_id: rangeId(item),
      label_type: type,
      start_time_seconds: Number(start.toFixed(3)),
      end_time_seconds: Number(end.toFixed(3)),
      center_time_seconds: Number(center.toFixed(3)),
      contact_estimate_time_seconds: Number(contact.toFixed(3)),
      start_frame_estimate: frameEstimate(start),
      end_frame_estimate: frameEstimate(end),
      contact_frame_estimate: frameEstimate(contact),
      fps_used: currentFps,
      confidence: item.confidence || "high",
      notes: item.notes || "",
    };
  });
  return {
    schema: "tennis_ai_vision.video_labels.v1",
    editor_version: EDITOR_VERSION,
    video_name: state.videoName,
    fps: currentFps,
    duration_seconds: Number(duration().toFixed(3)),
    timeline_zoom_at_export: Number(state.zoom.toFixed(3)),
    exported_at: new Date().toISOString(),
    labels: sortedLabels().map((label) => ({
      ...label,
      frame_estimate: frameEstimate(label.time_seconds),
      fps_used: currentFps,
    })),
    event_ranges: eventRanges,
    windows: sortedWindows().map((item) => ({
      ...item,
      label_type: `${normalizeRangeType(item.label_type)}_window`,
      start_frame_estimate: frameEstimate(item.start_time_seconds),
      end_frame_estimate: frameEstimate(item.end_time_seconds),
      center_frame_estimate: frameEstimate(contactEstimateTime(item)),
      fps_used: currentFps,
    })),
  };
}

function download(filename, mimeType, content) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportJson() {
  const name = state.videoName ? state.videoName.replace(/\W+/g, "_") : "video";
  download(`${name}_labels.json`, "application/json", `${JSON.stringify(exportPayload(), null, 2)}\n`);
}

function csvEscape(value) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function exportCsv() {
  const rows = sortedLabels();
  const header = ["label_id", "label_type", "time_seconds", "frame_estimate", "fps_used", "confidence", "notes"];
  const lines = [header.join(",")];
  rows.forEach((label) => {
    lines.push(header.map((field) => csvEscape(field === "frame_estimate" ? frameEstimate(label.time_seconds) : field === "fps_used" ? fps() : label[field])).join(","));
  });
  const name = state.videoName ? state.videoName.replace(/\W+/g, "_") : "video";
  download(`${name}_labels.csv`, "text/csv", `${lines.join("\n")}\n`);
}

videoInput.addEventListener("change", () => {
  const file = videoInput.files && videoInput.files[0];
  if (!file) {
    return;
  }
  if (state.objectUrl) {
    URL.revokeObjectURL(state.objectUrl);
  }
  state.objectUrl = URL.createObjectURL(file);
  state.videoName = file.name;
  state.thumbnails = [];
  video.src = state.objectUrl;
  state.zoom = 1;
  timelineViewport.scrollLeft = 0;
  render();
});

labelInput.addEventListener("change", async () => {
  const file = labelInput.files && labelInput.files[0];
  if (!file) {
    return;
  }
  const payload = JSON.parse(await file.text());
  if (payload.schema !== "tennis_ai_vision.video_labels.v1") {
    alert("Unsupported label schema.");
    return;
  }
  if (payload.fps) {
    fpsInput.value = String(payload.fps);
  }
  if (payload.timeline_zoom_at_export) {
    state.zoom = clamp(Number(payload.timeline_zoom_at_export), 1, 32);
  }
  state.videoName = payload.video_name || state.videoName;
  state.labels = Array.isArray(payload.labels) ? payload.labels : [];
  const importedRanges = Array.isArray(payload.event_ranges) ? payload.event_ranges : [];
  const importedWindows = Array.isArray(payload.windows) ? payload.windows : [];
  state.windows = (importedRanges.length ? importedRanges : importedWindows).map((item) => {
    const start = Number(item.start_time_seconds || 0);
    const end = Number(item.end_time_seconds || start);
    const center = Number(item.center_time_seconds || (start + end) / 2);
    const contact = Number(item.contact_estimate_time_seconds || center);
    const id = String(item.range_id || item.window_id || newId("range"));
    return {
      ...item,
      range_id: id,
      window_id: id,
      label_type: normalizeRangeType(item.label_type),
      start_time_seconds: Number(start.toFixed(3)),
      end_time_seconds: Number(end.toFixed(3)),
      center_time_seconds: Number(center.toFixed(3)),
      contact_estimate_time_seconds: Number(contact.toFixed(3)),
    };
  });
  state.selectedKind = "";
  state.selectedId = "";
  setStatus("Imported labels.");
  render();
});

video.addEventListener("loadedmetadata", () => {
  fitClip();
  generateThumbnails();
});
video.addEventListener("timeupdate", updatePlayhead);
video.addEventListener("play", renderTime);
video.addEventListener("pause", renderTime);
fpsInput.addEventListener("change", render);
timelineViewport.addEventListener("scroll", renderZoomStatus);
timelineViewport.addEventListener("pointerdown", beginScrub);
timelineViewport.addEventListener("pointermove", scrubMove);
timelineViewport.addEventListener("pointerup", endScrub);
timelineViewport.addEventListener("pointercancel", endScrub);
document.addEventListener("pointermove", updateDraggedRange);
document.addEventListener("pointerup", endRangeDrag);
document.addEventListener("pointercancel", endRangeDrag);
timelineViewport.addEventListener(
  "wheel",
  (event) => {
    if (event.altKey) {
      event.preventDefault();
      const factor = event.deltaY < 0 ? 1.18 : 1 / 1.18;
      setZoom(state.zoom * factor, event.clientX);
    } else if (event.ctrlKey || event.shiftKey) {
      event.preventDefault();
      timelineViewport.scrollLeft += event.deltaY || event.deltaX;
      renderZoomStatus();
    }
  },
  { passive: false },
);

document.getElementById("playPauseButton").addEventListener("click", togglePlayback);
document.getElementById("stepBackButton").addEventListener("click", () => step(-1 / fps()));
document.getElementById("stepForwardButton").addEventListener("click", () => step(1 / fps()));
document.getElementById("jumpBackButton").addEventListener("click", () => step(-10 / fps()));
document.getElementById("jumpForwardButton").addEventListener("click", () => step(10 / fps()));
document.getElementById("zoomOutButton").addEventListener("click", () => setZoom(state.zoom / 1.25));
document.getElementById("zoomInButton").addEventListener("click", () => setZoom(state.zoom * 1.25));
document.getElementById("fitClipButton").addEventListener("click", fitClip);
document.getElementById("setWindowStartButton").addEventListener("click", setWindowStart);
document.getElementById("setWindowEndButton").addEventListener("click", setWindowEnd);
document.getElementById("clearWindowButton").addEventListener("click", clearWindowSelection);
document.getElementById("exportJsonButton").addEventListener("click", exportJson);
document.getElementById("exportCsvButton").addEventListener("click", exportCsv);

document.querySelectorAll("[data-label]").forEach((button) => {
  button.addEventListener("click", () => addLabel(button.dataset.label));
});

document.querySelectorAll("[data-range-label]").forEach((button) => {
  button.addEventListener("click", () => {
    console.debug("range button clicked", { labelType: button.dataset.rangeLabel });
    addEventRange(button.dataset.rangeLabel);
  });
});

if (smokeTestButton) {
  smokeTestButton.addEventListener("click", () => {
    console.debug("smoke test result", window.__labelingEditorSmokeTest());
  });
}

document.querySelectorAll("[data-window-label]").forEach((button) => {
  button.addEventListener("click", () => saveWindow(button.dataset.windowLabel));
});

document.addEventListener("keydown", (event) => {
  const targetName = event.target && event.target.tagName ? event.target.tagName.toLowerCase() : "";
  if (["input", "select", "textarea"].includes(targetName)) {
    return;
  }
  const frameStep = 1 / fps();
  const jumpStep = 10 / fps();
  if (event.code === "Space") {
    event.preventDefault();
    togglePlayback();
  } else if (event.key.toLowerCase() === "a" || event.key === "ArrowLeft" || event.key === ",") {
    event.preventDefault();
    step(event.shiftKey ? -jumpStep : -frameStep);
  } else if (event.key.toLowerCase() === "d" || event.key === "ArrowRight" || event.key === ".") {
    event.preventDefault();
    step(event.shiftKey ? jumpStep : frameStep);
  } else if (event.key === "Home") {
    event.preventDefault();
    seekTime(0);
  } else if (event.key === "End") {
    event.preventDefault();
    seekTime(duration());
  } else if (event.key === "+" || event.key === "=") {
    event.preventDefault();
    setZoom(state.zoom * 1.25);
  } else if (event.key === "-") {
    event.preventDefault();
    setZoom(state.zoom / 1.25);
  } else if (event.key === "0") {
    event.preventDefault();
    fitClip();
  } else if (event.key.toLowerCase() === "s") {
    event.preventDefault();
    exportJson();
  } else if (event.key.toLowerCase() === "b") {
    event.preventDefault();
    addEventRange("bounce");
  } else if (event.key.toLowerCase() === "h") {
    event.preventDefault();
    addEventRange("hit");
  } else if (event.key.toLowerCase() === "n") {
    event.preventDefault();
    addEventRange("no_event");
  } else if (event.key.toLowerCase() === "u") {
    event.preventDefault();
    addEventRange("uncertain");
  } else if (event.key === "Delete") {
    event.preventDefault();
    deleteSelected();
  }
});

window.addEventListener("resize", renderTimeline);
window.__labelingEditorSmokeTest = function labelingEditorSmokeTest() {
  const result = {
    ok: false,
    rangeCount: state.windows.length,
    markerCount: windowLane.querySelectorAll(".event-range").length,
    lastError: null,
  };
  try {
    const before = state.windows.length;
    const beforeDom = result.markerCount;
    if (!video.src || !duration()) {
      result.lastError = "Load a video before adding ranges.";
      setStatus(result.lastError);
      setLastAction("Smoke test failed", result.lastError);
      return result;
    }
    addEventRange("bounce");
    result.rangeCount = state.windows.length;
    result.markerCount = windowLane.querySelectorAll(".event-range").length;
    result.ok = result.rangeCount === before + 1 && result.markerCount >= beforeDom + 1;
    result.lastError = result.ok ? null : "Range count or DOM marker count did not increase.";
    if (!result.ok) {
      setLastAction("Smoke test failed", result.lastError);
    }
    return {
      ok: result.ok,
      rangeCount: result.rangeCount,
      markerCount: result.markerCount,
      lastError: result.lastError,
    };
  } catch (error) {
    result.rangeCount = state.windows.length;
    result.markerCount = windowLane.querySelectorAll(".event-range").length;
    result.lastError = error instanceof Error ? error.message : String(error);
    setLastAction("Smoke test failed", result.lastError);
    return result;
  }
};
render();
