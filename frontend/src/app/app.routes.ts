import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'titles.home',
    loadComponent: () => import('./features/home/home.page').then((m) => m.HomePage),
  },
  {
    path: 'explorar',
    title: 'titles.places',
    loadComponent: () => import('./features/places/places-list.page').then((m) => m.PlacesListPage),
  },
  {
    path: 'lugares/:id',
    loadComponent: () =>
      import('./features/places/place-detail.page').then((m) => m.PlaceDetailPage),
  },
  {
    path: 'asistente',
    title: 'titles.assistant',
    loadComponent: () => import('./features/assistant/assistant.page').then((m) => m.AssistantPage),
  },
  {
    path: '**',
    title: 'titles.notFound',
    loadComponent: () => import('./features/not-found/not-found.page').then((m) => m.NotFoundPage),
  },
];
