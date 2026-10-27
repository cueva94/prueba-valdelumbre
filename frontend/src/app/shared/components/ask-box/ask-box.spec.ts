import { ComponentFixture, TestBed } from '@angular/core/testing';

import { provideTestTranslations } from '../../../../testing/translations';
import { AskBox } from './ask-box';

describe('AskBox', () => {
  let fixture: ComponentFixture<AskBox>;
  let submitted: string[];

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: provideTestTranslations() });
    fixture = TestBed.createComponent(AskBox);
    fixture.componentRef.setInput('label', 'Tu pregunta');
    submitted = [];
    fixture.componentInstance.submitted.subscribe((question) => submitted.push(question));
    fixture.detectChanges();
  });

  const element = () => fixture.nativeElement as HTMLElement;
  const field = () => element().querySelector('input') as HTMLInputElement;
  const submit = () =>
    (element().querySelector('button[type="submit"]') as HTMLButtonElement).click();

  function type(text: string): void {
    field().value = text;
    field().dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  it('no envía una pregunta vacía y explica por qué, de forma accesible', () => {
    type('   ');
    submit();
    fixture.detectChanges();

    expect(submitted).toEqual([]);
    expect(element().querySelector('[role="alert"]')?.textContent).toContain(
      'Escribe una pregunta',
    );
    expect(field().getAttribute('aria-invalid')).toBe('true');
    expect(document.activeElement).toBe(field());
  });

  it('envía la pregunta sin espacios sobrantes', () => {
    type('  ¿Qué museos hay?  ');
    submit();

    expect(submitted).toEqual(['¿Qué museos hay?']);
  });

  it('un tema rellena la pregunta sin enviarla', () => {
    fixture.componentRef.setInput('topics', [
      { labelKey: 'questions.topics.free.label', questionKey: 'questions.topics.free.question' },
    ]);
    fixture.detectChanges();

    const topic = element().querySelector('fieldset button') as HTMLButtonElement;
    expect(topic.textContent?.trim()).toBe('Gratis');
    topic.click();
    fixture.detectChanges();

    expect(field().value).toBe('¿Qué lugares se pueden visitar gratis?');
    expect(topic.getAttribute('aria-pressed')).toBe('true');
    expect(submitted).toEqual([]);
  });

  it('limita la pregunta a los 500 caracteres que admite la API', () => {
    expect(field().getAttribute('maxlength')).toBe('500');
  });
});
