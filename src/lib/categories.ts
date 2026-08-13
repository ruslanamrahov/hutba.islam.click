export const categoryLabels: Record<string, string> = {
  'zapretnye-deyaniya': 'Запретные деяния',
  'akida-i-manhadzh': 'Акида и манхадж',
  'ibadaty': 'Ибадаты',
  'prazdnichnye-hutby': 'Праздничные хутбы',
  'smyagcheniya-serdec': 'Смягчения сердец и увещевания',
  'zikry-i-molby': 'Зикры и мольбы',
  'spodvizhniki': 'Сподвижники',
  'sira': 'Сира',
  'raznoe': 'Разное',
  'general': 'Общие',
  'ramadan': 'Рамадан',
  'zul-hijjah': 'Зуль-хиджжа',
  'muharram': 'Мухаррам',
  'mawlid': 'Маулид',
  'shaban': "Ша'бан",
  'new-year': 'Новый год',
  'names-of-allah': 'Имена Аллаха',
  'aqida': 'Акыда и манхадж',
  'forbidden-deeds': 'Запретные деяния',
  'companions': 'Сподвижники',
};

export const categoryIcons: Record<string, string> = {
  'zapretnye-deyaniya': 'ن',
  'akida-i-manhadzh': 'ع',
  'ibadaty': 'ع',
  'smyagcheniya-serdec': 'ق',
  'zikry-i-molby': 'ذ',
  'spodvizhniki': 'ص',
  'sira': 'ﷺ',
  'raznoe': 'م',
  'general': 'ج',
  'ramadan': 'ر',
  'zul-hijjah': 'ح',
  'muharram': 'م',
  'mawlid': 'م',
  'shaban': 'ش',
  'names-of-allah': 'ا',
};

export function categoryLabel(slug: string): string {
  return categoryLabels[slug] || slug;
}

export function categoryIcon(slug: string): string {
  return categoryIcons[slug] || '•';
}

export function yearLabel(year: number): string {
  if (year <= 0) return 'Без года';
  return year < 2015 ? `До ${year + 1} года` : `${year} год`;
}
