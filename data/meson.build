subdir('logo')

desktop_file = i18n.merge_file(
  input: 'io.github.seadve.Kooha.desktop.in',
  output: 'io.github.seadve.Kooha.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

appstream_file = i18n.merge_file(
  input: 'io.github.seadve.Kooha.appdata.xml.in',
  output: 'io.github.seadve.Kooha.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate-relax', appstream_file]
  )
endif

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

install_data('io.github.seadve.Kooha.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

gnome = import('gnome')

kooha_sources += gnome.compile_resources('kooha-resources',
  'kooha.gresource.xml',
  c_name: 'kooha'
)
