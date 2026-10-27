import { TestBed } from '@angular/core/testing';

import { LANGUAGE_STORAGE_KEY, PreferencesStorage } from './preferences-storage.service';

describe('PreferencesStorage', () => {
  let preferences: PreferencesStorage;

  beforeEach(() => {
    preferences = TestBed.inject(PreferencesStorage);
  });

  afterEach(() => vi.restoreAllMocks());

  it('guarda y recupera el idioma', () => {
    expect(preferences.language()).toBeNull();

    preferences.saveLanguage('en');

    expect(localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe('en');
    expect(preferences.language()).toBe('en');
  });

  it.each(['fr', 'EN', 'english', ''])('un valor guardado no válido («%s») se ignora', (value) => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, value);

    expect(preferences.language()).toBeNull();
  });

  it('si el navegador no deja usar el almacenamiento, no falla', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('Bloqueado', 'SecurityError');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('Lleno', 'QuotaExceededError');
    });

    expect(preferences.language()).toBeNull();
    expect(() => preferences.saveLanguage('en')).not.toThrow();
  });
});
