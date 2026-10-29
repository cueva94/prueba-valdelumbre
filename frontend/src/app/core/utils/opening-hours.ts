/**
 * Formato del horario que publica cada ficha. Aquí no se decide si un lugar está abierto:
 * eso lo hace el backend (filtro `abierto_en`). Solo se presenta lo que dice la ficha, con los
 * nombres de días y meses del idioma activo.
 */

import { OpeningHours, Season } from '../models/poi.model';
import { Texts } from './texts';

const WEEKDAYS = [1, 2, 3, 4, 5, 6, 7] as const;
const MONTHS = Array.from({ length: 12 }, (_, month) => month);
const MIN_DAYS_FOR_RANGE = 3;

export interface DayRow {
  /** ISO 8601: 1 = lunes … 7 = domingo. */
  weekday: number;
  name: string;
  /** Tramos del día; vacío si ese día no abre (o no consta, si el horario está incompleto). */
  ranges: string[];
  isToday: boolean;
}

export function isHoursUnknown(hours: OpeningHours): boolean {
  return !hours.siempre_abierto && hours.franjas.length === 0;
}

export function hasSeason(hours: OpeningHours): boolean {
  return hours.franjas.some((slot) => slot.temporada !== null);
}

/** «Lun–Sáb · 10:00–14:00 y 17:00–20:00», «Abierto siempre» u «Horario no publicado». */
export function hoursSummary(hours: OpeningHours, texts: Texts): string {
  if (hours.siempre_abierto) {
    return texts.t('hours.alwaysOpen');
  }
  if (hours.franjas.length === 0) {
    return texts.t('hours.unpublished');
  }
  const rangesByDays = new Map<string, string[]>();
  for (const slot of hours.franjas) {
    const days = daysLabel(slot.dias, texts);
    rangesByDays.set(days, [...(rangesByDays.get(days) ?? []), `${slot.abre}–${slot.cierra}`]);
  }
  const summary = [...rangesByDays]
    .map(([days, ranges]) => `${days} · ${listOf(ranges, texts)}`)
    .join('; ');
  return hours.incompleto ? texts.t('hours.incomplete', { summary }) : summary;
}

/**
 * Una fila por día de la semana, de lunes a domingo. Si todas las franjas comparten temporada,
 * se indica una sola vez fuera de la tabla (`sharedSeason`); si no, cada tramo de temporada
 * lleva sus fechas.
 */
export function weeklySchedule(hours: OpeningHours, today: number, texts: Texts): DayRow[] {
  const datesPerRange = sharedSeason(hours) === null;
  return WEEKDAYS.map((weekday) => {
    const ranges = hours.franjas
      .filter((slot) => slot.dias.includes(weekday))
      .map((slot) => {
        const range = `${slot.abre} – ${slot.cierra}`;
        return slot.temporada && datesPerRange
          ? `${range} (${seasonText(slot.temporada, texts, 'inline')})`
          : range;
      });
    return { weekday, name: weekdayName(weekday, texts), ranges, isToday: weekday === today };
  });
}

export function sharedSeason(hours: OpeningHours): Season | null {
  const keys = new Set(hours.franjas.map((slot) => seasonKey(slot.temporada)));
  return keys.size === 1 ? hours.franjas[0].temporada : null;
}

export function seasonsOf(hours: OpeningHours): Season[] {
  const seasons = new Map<string, Season>();
  for (const slot of hours.franjas) {
    if (slot.temporada) {
      seasons.set(seasonKey(slot.temporada), slot.temporada);
    }
  }
  return [...seasons.values()];
}

/** «Del 1 de junio al 30 de septiembre» o, dentro de una frase, «del 1 de junio al…». */
export function seasonText(
  season: Season,
  texts: Texts,
  position: 'start' | 'inline' = 'start',
): string {
  return texts.t(position === 'inline' ? 'hours.seasonInline' : 'hours.season', {
    start: dayAndMonth(season.inicio, texts),
    end: dayAndMonth(season.fin, texts),
  });
}

/** Para cada mes (enero = 0), si alguna temporada del horario incluye algún día de ese mes. */
export function seasonMonths(hours: OpeningHours): boolean[] {
  const months = Array<boolean>(12).fill(false);
  for (const season of seasonsOf(hours)) {
    const start = monthOf(season.inicio);
    const end = monthOf(season.fin);
    for (let offset = 0; offset < 12; offset++) {
      const month = (start + offset) % 12;
      months[month] = true;
      if (month === end) {
        break;
      }
    }
  }
  return months;
}

export function weekdayNames(texts: Texts): string[] {
  return WEEKDAYS.map((weekday) => weekdayName(weekday, texts));
}

export function months(texts: Texts): { name: string; initial: string }[] {
  return MONTHS.map((month) => ({
    name: formatDate(Date.UTC(2024, month, 15), { month: 'long' }, texts),
    initial: formatDate(Date.UTC(2024, month, 15), { month: 'narrow' }, texts),
  }));
}

/** Día de la semana ISO en Valdelumbre (Europe/Madrid), sea cual sea la zona del navegador. */
export function weekdayInTown(date: Date = new Date()): number {
  const weekday = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Madrid',
    weekday: 'short',
  }).format(date);
  return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].indexOf(weekday) + 1;
}

/** «Todos los días», «Lun–Sáb» o «Vie y Sáb». */
function daysLabel(days: number[], texts: Texts): string {
  const sorted = [...new Set(days)].sort((a, b) => a - b);
  if (sorted.length === WEEKDAYS.length) {
    return texts.t('hours.everyDay');
  }
  const short = (day: number) => weekdayName(day, texts, 'short');
  const isRun = sorted.every((day, index) => index === 0 || day === sorted[index - 1] + 1);
  if (isRun && sorted.length >= MIN_DAYS_FOR_RANGE) {
    return `${short(sorted[0])}–${short(sorted[sorted.length - 1])}`;
  }
  return listOf(sorted.map(short), texts);
}

/** 1 = lunes; el 1 de enero de 2024 fue lunes. */
function weekdayName(weekday: number, texts: Texts, width: 'long' | 'short' = 'long'): string {
  const name = formatDate(Date.UTC(2024, 0, weekday), { weekday: width }, texts);
  return name.charAt(0).toLocaleUpperCase(texts.locale()) + name.slice(1);
}

function formatDate(time: number, options: Intl.DateTimeFormatOptions, texts: Texts): string {
  return new Intl.DateTimeFormat(texts.locale(), { ...options, timeZone: 'UTC' }).format(time);
}

function listOf(items: string[], texts: Texts): string {
  return new Intl.ListFormat(texts.locale(), { type: 'conjunction' }).format(items);
}

function seasonKey(season: Season | null): string {
  return season ? `${season.inicio}/${season.fin}` : '';
}

function monthOf(monthDay: string): number {
  return Number(monthDay.slice(0, 2)) - 1;
}

/** «06-01» → «1 de junio» / «1 June». */
function dayAndMonth(monthDay: string, texts: Texts): string {
  return formatDate(
    Date.UTC(2024, monthOf(monthDay), Number(monthDay.slice(3, 5))),
    { day: 'numeric', month: 'long' },
    texts,
  );
}
