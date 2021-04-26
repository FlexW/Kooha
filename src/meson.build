kooha_sources += [
  'main.vala',
  'window.vala',
]

kooha_deps = [
  dependency('gio-2.0'),
  dependency('gtk4'),
  dependency('libadwaita-1')
]

gnome = import('gnome')

executable('kooha', kooha_sources,
  vala_args: '--target-glib=2.50',
  dependencies: kooha_deps,
  install: true,
)
