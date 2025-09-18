import "https://cdn.jsdelivr.net/npm/dayjs@1.11.10/locale/zh-cn.js";

dayjs.extend(window.dayjs_plugin_utc);
dayjs.extend(window.dayjs_plugin_timezone);
dayjs.locale("zh-cn");

const calendarEl = document.getElementById("calendar");
const dialog = document.getElementById("event-dialog");
const openDialogBtn = document.getElementById("open-dialog");
const form = document.getElementById("event-form");
const deleteButton = document.getElementById("delete-button");
const cancelButton = document.getElementById("cancel-button");
const submitButton = document.getElementById("submit-button");
const toastTemplate = document.getElementById("toast-template");

const getInput = (id) => document.getElementById(id);
const inputTitle = getInput("title");
const inputCategory = getInput("category");
const inputLocation = getInput("location");
const inputStart = getInput("start_time");
const inputEnd = getInput("end_time");
const inputReminderEmail = getInput("reminder_email");
const inputReminderMinutes = getInput("reminder_minutes_before");
const inputDescription = getInput("description");
const inputId = getInput("event-id");

let calendar;

function showToast(title, message, variant = "primary") {
  const alert = toastTemplate.content.firstElementChild.cloneNode(true);
  alert.variant = variant;
  alert.querySelector(".toast-title").textContent = title;
  alert.querySelector(".toast-message").textContent = message;
  document.body.append(alert);
  alert.toast();
}

function clearForm() {
  inputId.value = "";
  form.reset();
  deleteButton.hidden = true;
  dialog.label = "新增行程";
}

function openFormDialog(eventData = null) {
  if (!eventData) {
    clearForm();
    dialog.label = "新增行程";
    dialog.show();
    return;
  }
  dialog.label = "编辑行程";
  inputId.value = eventData.id;
  inputTitle.value = eventData.title;
  inputCategory.value = eventData.category ?? "";
  inputLocation.value = eventData.location ?? "";
  inputReminderEmail.value = eventData.reminder_email ?? "";
  inputReminderMinutes.value = eventData.reminder_minutes_before ?? "";
  inputDescription.value = eventData.description ?? "";
  inputStart.value = dayjs(eventData.start).local().format("YYYY-MM-DDTHH:mm");
  inputEnd.value = dayjs(eventData.end).local().format("YYYY-MM-DDTHH:mm");
  deleteButton.hidden = false;
  dialog.show();
}

async function fetchEvents(fetchInfo, successCallback, failureCallback) {
  const params = new URLSearchParams();
  if (fetchInfo.startStr) {
    params.set("start_after", dayjs(fetchInfo.start).toISOString());
  }
  if (fetchInfo.endStr) {
    params.set("end_before", dayjs(fetchInfo.end).toISOString());
  }
  try {
    const response = await fetch(`/events?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`加载行程失败: ${response.status}`);
    }
    const data = await response.json();
    const events = data.map((item) => ({
      id: String(item.id),
      title: item.title,
      start: item.start_time,
      end: item.end_time,
      extendedProps: item,
    }));
    successCallback(events);
  } catch (error) {
    console.error(error);
    failureCallback(error);
    showToast("加载失败", error.message, "danger");
  }
}

async function createEvent(payload) {
  const response = await fetch("/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? "创建行程失败");
  }
  return response.json();
}

async function updateEvent(id, payload) {
  const response = await fetch(`/events/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? "更新行程失败");
  }
  return response.json();
}

async function deleteEvent(id) {
  const response = await fetch(`/events/${id}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? "删除行程失败");
  }
}

function toUtcIso(datetimeLocalValue) {
  // datetime-local 没有时区信息，按本地时区解释并转换为 ISO 带时区
  return dayjs.tz(datetimeLocalValue, dayjs.tz.guess()).toISOString();
}

function validateReminderFields(reminderEmail, reminderMinutes) {
  if (reminderEmail && (reminderMinutes === null || reminderMinutes === "")) {
    throw new Error("设置提醒邮箱时必须填写提前提醒分钟数");
  }
  if (!reminderEmail && reminderMinutes) {
    throw new Error("设置提前提醒分钟数时必须填写提醒邮箱");
  }
}

function collectFormPayload() {
  const title = inputTitle.value.trim();
  const start = inputStart.value;
  const end = inputEnd.value;
  if (!title) {
    throw new Error("标题不能为空");
  }
  validateReminderFields(inputReminderEmail.value.trim(), inputReminderMinutes.value.trim());
  const payload = {
    title,
    description: inputDescription.value.trim() || null,
    category: inputCategory.value.trim() || null,
    location: inputLocation.value.trim() || null,
    start_time: toUtcIso(start),
    end_time: toUtcIso(end),
    reminder_email: inputReminderEmail.value.trim() || null,
    reminder_minutes_before: inputReminderMinutes.value ? Number(inputReminderMinutes.value) : null,
  };
  return payload;
}

function initializeCalendar() {
  calendar = new FullCalendar.Calendar(calendarEl, {
    height: "auto",
    initialView: "dayGridMonth",
    locale: "zh-cn",
    selectable: true,
    editable: true,
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
    },
    eventSources: [fetchEvents],
    eventDidMount(info) {
      if (!info.view.type.startsWith("list")) {
        return;
      }
      const titleEl = info.el.querySelector(".fc-list-event-title");
      if (!titleEl || titleEl.querySelector(".list-delete-btn")) {
        return;
      }
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "list-delete-btn";
      deleteBtn.innerHTML = "<span>删除</span>";
      deleteBtn.addEventListener("click", async (evt) => {
        evt.preventDefault();
        evt.stopPropagation();
        if (!window.confirm("确定要删除该行程吗？")) {
          return;
        }
        try {
          await deleteEvent(info.event.id);
          showToast("删除成功", "行程已删除", "success");
          info.event.remove();
        } catch (error) {
          showToast("删除失败", error.message, "danger");
        }
      });
      titleEl.appendChild(deleteBtn);
    },
    dateClick(info) {
      clearForm();
      const local = dayjs(info.dateStr).hour(dayjs().hour()).minute(0);
      inputStart.value = local.format("YYYY-MM-DDTHH:mm");
      inputEnd.value = local.add(1, "hour").format("YYYY-MM-DDTHH:mm");
      dialog.show();
    },
    eventClick(info) {
      info.jsEvent.preventDefault();
      const data = info.event.extendedProps;
      data.id = info.event.id;
      data.start = info.event.start;
      data.end = info.event.end;
      openFormDialog(data);
    },
    eventDrop(info) {
      handleScheduleChange(info, "已拖动到新时间段");
    },
    eventResize(info) {
      handleScheduleChange(info, "已调整结束时间");
    },
  });
  calendar.render();
}

async function handleScheduleChange(info, successMessage) {
  const id = info.event.id;
  try {
    await updateEvent(id, {
      start_time: dayjs(info.event.start).toISOString(),
      end_time: dayjs(info.event.end).toISOString(),
    });
    showToast("更新成功", successMessage, "success");
  } catch (error) {
    info.revert();
    showToast("更新失败", error.message, "danger");
  }
}

openDialogBtn.addEventListener("click", () => {
  clearForm();
  const now = dayjs();
  inputStart.value = now.format("YYYY-MM-DDTHH:mm");
  inputEnd.value = now.add(1, "hour").format("YYYY-MM-DDTHH:mm");
  dialog.show();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = collectFormPayload();
    if (inputId.value) {
      await updateEvent(inputId.value, payload);
      showToast("更新成功", "行程已更新", "success");
    } else {
      await createEvent(payload);
      showToast("创建成功", "行程已创建", "success");
    }
    dialog.hide();
    calendar.refetchEvents();
  } catch (error) {
    showToast("保存失败", error.message, "danger");
  }
});

cancelButton.addEventListener("click", () => {
  dialog.hide();
});

submitButton.addEventListener("click", () => {
  form.requestSubmit();
});

deleteButton.addEventListener("click", async () => {
  if (!inputId.value) return;
  const confirmed = window.confirm("确定要删除该行程吗？");
  if (!confirmed) {
    return;
  }
  try {
    await deleteEvent(inputId.value);
    showToast("删除成功", "行程已删除", "success");
    const existing = calendar.getEventById(inputId.value);
    if (existing) {
      existing.remove();
    }
    dialog.hide();
    setTimeout(() => {
      calendar.refetchEvents();
    }, 150);
  } catch (error) {
    showToast("删除失败", error.message, "danger");
  }
});

initializeCalendar();
