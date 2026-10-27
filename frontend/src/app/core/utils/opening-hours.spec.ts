import { CASTLE, HERMITAGE, NATURAL_POOL, OIL_MUSEUM } from '../../../testing/pois';
import { languageIn } from '../../../testing/translations';
import { OpeningHours } from '../models/poi.model';
import { LanguageService } from '../services/language.service';
import {
  hoursSummary,
  isHoursUnknown,
  months,
  seasonMonths,
  seasonText,
  sharedSeason,
  weekdayInTown,
  weeklySchedule,
} from './opening-hours';

const ALWAYS_OPEN: OpeningHours = { siempre_abierto: true, franjas: [], incompleto: false };

let es: LanguageService;

beforeEach(async () => {
  es = await languageIn('es');
});

describe('hoursSummary', () => {
  it('agrupa los días que comparten horario', () => {
    expect(hoursSummary(CASTLE.horario, es)).toBe('Lun–Sáb · 10:00–14:00 y 17:00–20:00');
  });

  it('no inventa horas: «Abierto siempre» u «Horario no publicado»', () => {
    expect(hoursSummary(ALWAYS_OPEN, es)).toBe('Abierto siempre');
    expect(hoursSummary(HERMITAGE.horario, es)).toBe('Horario no publicado');
    expect(isHoursUnknown(HERMITAGE.horario)).toBe(true);
    expect(isHoursUnknown(ALWAYS_OPEN)).toBe(false);
  });

  it('separa los grupos de días distintos y avisa si el horario está incompleto', () => {
    const restaurant: OpeningHours = {
      siempre_abierto: false,
      incompleto: true,
      franjas: [
        { dias: [1, 2, 3, 4, 5, 6, 7], abre: '13:00', cierra: '16:30', temporada: null },
        { dias: [5, 6], abre: '20:30', cierra: '23:30', temporada: null },
      ],
    };

    expect(hoursSummary(restaurant, es)).toBe(
      'Todos los días · 13:00–16:30; Vie y Sáb · 20:30–23:30 (horario incompleto)',
    );
  });
});

describe('weeklySchedule', () => {
  it('da una fila por día, de lunes a domingo, con «hoy» marcado', () => {
    const rows = weeklySchedule(OIL_MUSEUM.horario, 1, es);

    expect(rows.map((row) => row.name)).toEqual([
      'Lunes',
      'Martes',
      'Miércoles',
      'Jueves',
      'Viernes',
      'Sábado',
      'Domingo',
    ]);
    expect(rows[0]).toEqual({ weekday: 1, name: 'Lunes', ranges: [], isToday: true });
    expect(rows[1].ranges).toEqual(['10:00 – 18:00']);
  });

  it('si todo el horario es de una misma temporada, no la repite en cada tramo', () => {
    expect(weeklySchedule(NATURAL_POOL.horario, 3, es)[0].ranges).toEqual(['11:00 – 20:00']);
    expect(sharedSeason(NATURAL_POOL.horario)).toEqual({ inicio: '06-01', fin: '09-30' });
  });

  it('si se mezclan tramos de temporada y de todo el año, cada tramo de temporada lleva sus fechas', () => {
    const mixed: OpeningHours = {
      siempre_abierto: false,
      incompleto: false,
      franjas: [
        { dias: [6, 7], abre: '10:00', cierra: '14:00', temporada: null },
        { dias: [6], abre: '17:00', cierra: '21:00', temporada: { inicio: '07-01', fin: '08-31' } },
      ],
    };

    expect(sharedSeason(mixed)).toBeNull();
    expect(weeklySchedule(mixed, 1, es)[5].ranges).toEqual([
      '10:00 – 14:00',
      '17:00 – 21:00 (del 1 de julio al 31 de agosto)',
    ]);
    expect(weeklySchedule(mixed, 1, es)[6].ranges).toEqual(['10:00 – 14:00']);
  });
});

describe('temporadas', () => {
  it('describe la temporada en palabras', () => {
    expect(seasonText({ inicio: '06-01', fin: '09-30' }, es)).toBe(
      'Del 1 de junio al 30 de septiembre',
    );
    expect(seasonText({ inicio: '06-01', fin: '09-30' }, es, 'inline')).toBe(
      'del 1 de junio al 30 de septiembre',
    );
  });

  it('marca los meses de temporada, también si cruza el fin de año', () => {
    const winter: OpeningHours = {
      siempre_abierto: false,
      incompleto: false,
      franjas: [
        { dias: [6], abre: '10:00', cierra: '14:00', temporada: { inicio: '11-15', fin: '02-28' } },
      ],
    };

    expect(seasonMonths(NATURAL_POOL.horario).map(Number)).toEqual([
      0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0,
    ]);
    expect(seasonMonths(winter).map(Number)).toEqual([1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1]);
  });
});

describe('en inglés', () => {
  let en: LanguageService;

  beforeEach(async () => {
    en = es;
    await en.use('en');
  });

  it('usa los días, meses, listas y textos del inglés', () => {
    expect(hoursSummary(CASTLE.horario, en)).toBe('Mon–Sat · 10:00–14:00 and 17:00–20:00');
    expect(hoursSummary(HERMITAGE.horario, en)).toBe('Opening hours not published');
    expect(weeklySchedule(OIL_MUSEUM.horario, 1, en)[0].name).toBe('Monday');
    expect(seasonText({ inicio: '06-01', fin: '09-30' }, en)).toBe('From 1 June to 30 September');
    expect(months(en)[0]).toEqual({ name: 'January', initial: 'J' });
  });
});

describe('weekdayInTown', () => {
  it('usa la hora de Valdelumbre (Europe/Madrid), no la del navegador', () => {
    // El 25/10/2026 a las 23:30 UTC ya es lunes 26 a las 00:30 en Madrid.
    expect(weekdayInTown(new Date('2026-10-25T23:30:00Z'))).toBe(1);
    expect(weekdayInTown(new Date('2026-10-25T12:00:00Z'))).toBe(7);
  });
});
