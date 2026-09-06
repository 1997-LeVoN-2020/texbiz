"""Контурные значки 24×24 (только path-данные). Перенесены со старого сайта скриптом scripts/import_old_site.py."""

ICON_PATHS = {
    '1C': '<ellipse cx="12" cy="6" rx="7" ry="2.5"/><path d="M5 6v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6"/><path d="M5 12v6c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-6"/>',
    'KKT': '<path d="M7 3h10v18l-2-1.5-2 1.5-2-1.5-2 1.5-2-1.5V3z"/><path d="M9 7h6M9 10h6M9 13h4"/>',
    'RPT': '<path d="M4 16l5-5 4 3 6-7"/><path d="M4 20h16"/>',
    'OTA': '<path d="M20 11A8 8 0 006.3 6.3M4 13a8 8 0 0013.7 4.7"/><path d="M4 4v5h5M20 20v-5h-5"/>',
    'PMS': '<path d="M20 11A8 8 0 006.3 6.3M4 13a8 8 0 0013.7 4.7"/><path d="M4 4v5h5M20 20v-5h-5"/>',
    'EDU': '<path d="M12 6c-2-1.5-5-2-8-1v13c3-1 6-.5 8 1 2-1.5 5-2 8-1V5c-3-1-6-.5-8 1z"/><path d="M12 6v13"/>',
    'OPS': '<path d="M4 13v-1a8 8 0 0116 0v1"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/><path d="M20 19v1a3 3 0 01-3 3h-3"/>',
    'BOOK': '<rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/><path d="M9 15l2 2 4-4"/>',
    'PAY': '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18"/><path d="M7 14h4"/>',
    '15': '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2"/><path d="M9 2h6"/>',
    'SRCH': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M20 20l-4.8-4.8"/>',
    'RUM': '<path d="M3 19v-7a3 3 0 013-3h12a3 3 0 013 3v7"/><path d="M3 15h18"/><path d="M7 12v-1a2 2 0 012-2h2a2 2 0 012 2v1"/>',
    'KID': '<circle cx="9" cy="7" r="3.2"/><path d="M3.5 20v-1.2A5.3 5.3 0 018.8 13.5h.4a5.3 5.3 0 015.3 5.3V20"/><circle cx="18" cy="10" r="2.2"/><path d="M14.8 20v-.9a3.7 3.7 0 013.7-3.7 3.7 3.7 0 013.7 3.7"/>',
    'CRT': '<rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="8" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/><rect x="13" y="13" width="8" height="8" rx="1.5"/>',
    'ADM': '<circle cx="12" cy="12" r="3"/><path d="M12 3v2.2M12 18.8V21M4.9 4.9l1.6 1.6M17.5 17.5l1.6 1.6M3 12h2.2M18.8 12H21M4.9 19.1l1.6-1.6M17.5 6.5l1.6-1.6"/>',
    'OFD': '<path d="M7 18a4.5 4.5 0 01-.7-8.9A5.5 5.5 0 0117 8.5 4 4 0 0117 17H7z"/><path d="M12 14V9M9.5 11.5L12 9l2.5 2.5"/>',
    'RES': '<rect x="4" y="7" width="12" height="12" rx="1.5"/><path d="M8 7V6a2 2 0 012-2h9a2 2 0 012 2v9a2 2 0 01-2 2h-1"/>',
    'SRV': '<rect x="4" y="4" width="16" height="6" rx="1.2"/><rect x="4" y="14" width="16" height="6" rx="1.2"/><path d="M7.5 7h.01M7.5 17h.01"/>',
    'WIFI': '<path d="M4 9a13 13 0 0116 0"/><path d="M7.2 12.6a8.5 8.5 0 019.6 0"/><path d="M10 16.2a4 4 0 014 0"/><circle cx="12" cy="19.2" r="0.9" fill="currentColor" stroke="none"/>',
    'MON': '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M6 11h3l1.5-3 2 6 1.5-3H18"/>',
    'SEC': '<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9.2 12.2l1.9 1.9 3.7-3.7"/>',
    'SCL': '<path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5"/>',
    'LOCK': '<rect x="5" y="10" width="14" height="10" rx="2"/><path d="M8 10V7a4 4 0 018 0v3"/><circle cx="12" cy="15" r="1.4" fill="currentColor" stroke="none"/>',
    'CARD': '<rect x="3" y="5" width="18" height="14" rx="2"/><rect x="6" y="9" width="4" height="3" rx="0.6"/><path d="M6 15h5M6 17h3"/>',
    'CMP': '<path d="M9 2v5M15 2v5M7 7h10v3a5 5 0 01-10 0z"/><path d="M12 15v3M9 21h6"/>',
    'LOG': '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 3h6v3H9z"/><path d="M9 11h6M9 14h6M9 17h4"/>',
    'ZON': '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/><rect x="9" y="9" width="6" height="6" fill="currentColor" stroke="none" opacity="0.15"/>',
    'MIG': '<rect x="2" y="8" width="6" height="8" rx="1"/><rect x="16" y="8" width="6" height="8" rx="1"/><path d="M9 12h6M12.5 9.5L15 12l-2.5 2.5"/>',
}

ICON_CHOICES = [(code, code) for code in ICON_PATHS]
