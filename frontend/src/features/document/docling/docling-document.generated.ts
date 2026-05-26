import { z } from 'zod'

export const doclingDocument = z
  .object({
    body: z
      .object({
        children: z
          .array(
            z
              .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
              .describe('RefItem.'),
          )
          .default([]),
        content_layer: z
          .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
          .describe('ContentLayer.')
          .default('body'),
        label: z
          .enum([
            'unspecified',
            'list',
            'ordered_list',
            'chapter',
            'section',
            'sheet',
            'slide',
            'form_area',
            'key_value_area',
            'comment_section',
            'inline',
            'picture_area',
          ])
          .describe('GroupLabel.')
          .default('unspecified'),
        meta: z
          .union([
            z
              .object({
                entities: z
                  .union([
                    z
                      .object({
                        mentions: z
                          .array(
                            z
                              .object({
                                charspan: z
                                  .union([
                                    z
                                      .array(z.any())
                                      .min(2)
                                      .max(2)
                                      .describe('Character span (0-indexed)'),
                                    z.null(),
                                  ])
                                  .describe(
                                    'Character span (0-indexed) of the entity mention in the source text.',
                                  )
                                  .default(null),
                                confidence: z
                                  .union([z.number().gte(0).lte(1), z.null()])
                                  .describe('The confidence of the prediction.')
                                  .default(null),
                                created_by: z
                                  .union([z.string(), z.null()])
                                  .describe('The origin of the prediction.')
                                  .default(null),
                                label: z
                                  .union([z.string(), z.null()])
                                  .describe('Entity type or category.')
                                  .default(null),
                                orig: z
                                  .union([z.string(), z.null()])
                                  .describe(
                                    "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                  )
                                  .default(null),
                                text: z.string().describe('Normalized text of the entity mention.'),
                              })
                              .catchall(z.any())
                              .describe('Entity mention extracted from text.'),
                          )
                          .min(1),
                      })
                      .catchall(z.any())
                      .describe('Container for extracted entity mentions.'),
                    z.null(),
                  ])
                  .default(null),
                language: z
                  .union([
                    z
                      .object({
                        code: z
                          .enum([
                            'aa',
                            'ab',
                            'ae',
                            'af',
                            'ak',
                            'am',
                            'an',
                            'ar',
                            'as',
                            'av',
                            'ay',
                            'az',
                            'ba',
                            'be',
                            'bg',
                            'bh',
                            'bi',
                            'bm',
                            'bn',
                            'bo',
                            'br',
                            'bs',
                            'ca',
                            'ce',
                            'ch',
                            'co',
                            'cr',
                            'cs',
                            'cu',
                            'cv',
                            'cy',
                            'da',
                            'de',
                            'dv',
                            'dz',
                            'ee',
                            'el',
                            'en',
                            'eo',
                            'es',
                            'et',
                            'eu',
                            'fa',
                            'ff',
                            'fi',
                            'fj',
                            'fo',
                            'fr',
                            'fy',
                            'ga',
                            'gd',
                            'gl',
                            'gn',
                            'gu',
                            'gv',
                            'ha',
                            'he',
                            'hi',
                            'ho',
                            'hr',
                            'ht',
                            'hu',
                            'hy',
                            'hz',
                            'ia',
                            'id',
                            'ie',
                            'ig',
                            'ii',
                            'ik',
                            'io',
                            'is',
                            'it',
                            'iu',
                            'ja',
                            'jv',
                            'ka',
                            'kg',
                            'ki',
                            'kj',
                            'kk',
                            'kl',
                            'km',
                            'kn',
                            'ko',
                            'kr',
                            'ks',
                            'ku',
                            'kv',
                            'kw',
                            'ky',
                            'la',
                            'lb',
                            'lg',
                            'li',
                            'ln',
                            'lo',
                            'lt',
                            'lu',
                            'lv',
                            'mg',
                            'mh',
                            'mi',
                            'mk',
                            'ml',
                            'mn',
                            'mr',
                            'ms',
                            'mt',
                            'my',
                            'na',
                            'nb',
                            'nd',
                            'ne',
                            'ng',
                            'nl',
                            'nn',
                            'no',
                            'nr',
                            'nv',
                            'ny',
                            'oc',
                            'oj',
                            'om',
                            'or',
                            'os',
                            'pa',
                            'pi',
                            'pl',
                            'ps',
                            'pt',
                            'qu',
                            'rm',
                            'rn',
                            'ro',
                            'ru',
                            'rw',
                            'sa',
                            'sc',
                            'sd',
                            'se',
                            'sg',
                            'sh',
                            'si',
                            'sk',
                            'sl',
                            'sm',
                            'sn',
                            'so',
                            'sq',
                            'sr',
                            'ss',
                            'st',
                            'su',
                            'sv',
                            'sw',
                            'ta',
                            'te',
                            'tg',
                            'th',
                            'ti',
                            'tk',
                            'tl',
                            'tn',
                            'to',
                            'tr',
                            'ts',
                            'tt',
                            'tw',
                            'ty',
                            'ug',
                            'uk',
                            'ur',
                            'uz',
                            've',
                            'vi',
                            'vo',
                            'wa',
                            'wo',
                            'xh',
                            'yi',
                            'yo',
                            'za',
                            'zh',
                            'zu',
                          ])
                          .describe(
                            'Two-letter human language primary subtags using BCP-47 values.',
                          ),
                        confidence: z
                          .union([z.number().gte(0).lte(1), z.null()])
                          .describe('The confidence of the prediction.')
                          .default(null),
                        created_by: z
                          .union([z.string(), z.null()])
                          .describe('The origin of the prediction.')
                          .default(null),
                      })
                      .catchall(z.any())
                      .describe('Detected human language.'),
                    z.null(),
                  ])
                  .default(null),
                summary: z
                  .union([
                    z
                      .object({
                        confidence: z
                          .union([z.number().gte(0).lte(1), z.null()])
                          .describe('The confidence of the prediction.')
                          .default(null),
                        created_by: z
                          .union([z.string(), z.null()])
                          .describe('The origin of the prediction.')
                          .default(null),
                        text: z.string(),
                      })
                      .catchall(z.any())
                      .describe('Summary data.'),
                    z.null(),
                  ])
                  .default(null),
              })
              .catchall(z.any())
              .describe('Base class for metadata.'),
            z.null(),
          ])
          .default(null),
        name: z.string().default('group'),
        parent: z
          .union([
            z
              .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
              .describe('RefItem.'),
            z.null(),
          ])
          .default(null),
        self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
      })
      .strict()
      .describe('GroupItem.')
      .default({
        children: [],
        content_layer: 'body',
        label: 'unspecified',
        meta: null,
        name: '_root_',
        parent: null,
        self_ref: '#/body',
      }),
    field_items: z
      .array(
        z
          .object({
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            label: z.literal('field_item').default('field_item'),
            meta: z
              .union([
                z
                  .object({
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Base class for metadata.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict(),
      )
      .default([]),
    field_regions: z
      .array(
        z
          .object({
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            label: z.literal('field_region').default('field_region'),
            meta: z
              .union([
                z
                  .object({
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Base class for metadata.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict(),
      )
      .default([]),
    form_items: z
      .array(
        z
          .object({
            captions: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            footnotes: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            graph: z
              .object({
                cells: z
                  .array(
                    z
                      .object({
                        cell_id: z.number().int(),
                        item_ref: z
                          .union([
                            z
                              .object({
                                $ref: z
                                  .string()
                                  .regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                              })
                              .describe('RefItem.'),
                            z.null(),
                          ])
                          .default(null),
                        label: z
                          .enum(['unspecified', 'key', 'value', 'checkbox'])
                          .describe('GraphCellLabel.'),
                        orig: z.string(),
                        prov: z
                          .union([
                            z
                              .object({
                                bbox: z
                                  .object({
                                    b: z.number(),
                                    coord_origin: z
                                      .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                      .describe('CoordOrigin.')
                                      .default('TOPLEFT'),
                                    l: z.number(),
                                    r: z.number(),
                                    t: z.number(),
                                  })
                                  .describe('Bounding box'),
                                charspan: z
                                  .array(z.any())
                                  .min(2)
                                  .max(2)
                                  .describe('Character span (0-indexed)'),
                                page_no: z.number().int().describe('Page number'),
                              })
                              .describe(
                                'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                              ),
                            z.null(),
                          ])
                          .default(null),
                        text: z.string(),
                      })
                      .describe('GraphCell.'),
                  )
                  .optional(),
                links: z
                  .array(
                    z
                      .object({
                        label: z
                          .enum(['unspecified', 'to_value', 'to_key', 'to_parent', 'to_child'])
                          .describe('GraphLinkLabel.'),
                        source_cell_id: z.number().int(),
                        target_cell_id: z.number().int(),
                      })
                      .describe('GraphLink.'),
                  )
                  .optional(),
              })
              .describe('GraphData.'),
            image: z
              .union([
                z
                  .object({
                    dpi: z.number().int(),
                    mimetype: z.string(),
                    size: z
                      .object({ height: z.number().default(0), width: z.number().default(0) })
                      .describe('Size.'),
                    uri: z.union([z.string().url().min(1), z.string()]),
                  })
                  .describe('ImageRef.'),
                z.null(),
              ])
              .default(null),
            label: z.literal('form').default('form'),
            meta: z
              .union([
                z
                  .object({
                    description: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Description metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Metadata model for floating.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            references: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict()
          .describe('FormItem.'),
      )
      .default([]),
    furniture: z
      .object({
        children: z
          .array(
            z
              .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
              .describe('RefItem.'),
          )
          .default([]),
        content_layer: z
          .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
          .describe('ContentLayer.')
          .default('body'),
        label: z
          .enum([
            'unspecified',
            'list',
            'ordered_list',
            'chapter',
            'section',
            'sheet',
            'slide',
            'form_area',
            'key_value_area',
            'comment_section',
            'inline',
            'picture_area',
          ])
          .describe('GroupLabel.')
          .default('unspecified'),
        meta: z
          .union([
            z
              .object({
                entities: z
                  .union([
                    z
                      .object({
                        mentions: z
                          .array(
                            z
                              .object({
                                charspan: z
                                  .union([
                                    z
                                      .array(z.any())
                                      .min(2)
                                      .max(2)
                                      .describe('Character span (0-indexed)'),
                                    z.null(),
                                  ])
                                  .describe(
                                    'Character span (0-indexed) of the entity mention in the source text.',
                                  )
                                  .default(null),
                                confidence: z
                                  .union([z.number().gte(0).lte(1), z.null()])
                                  .describe('The confidence of the prediction.')
                                  .default(null),
                                created_by: z
                                  .union([z.string(), z.null()])
                                  .describe('The origin of the prediction.')
                                  .default(null),
                                label: z
                                  .union([z.string(), z.null()])
                                  .describe('Entity type or category.')
                                  .default(null),
                                orig: z
                                  .union([z.string(), z.null()])
                                  .describe(
                                    "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                  )
                                  .default(null),
                                text: z.string().describe('Normalized text of the entity mention.'),
                              })
                              .catchall(z.any())
                              .describe('Entity mention extracted from text.'),
                          )
                          .min(1),
                      })
                      .catchall(z.any())
                      .describe('Container for extracted entity mentions.'),
                    z.null(),
                  ])
                  .default(null),
                language: z
                  .union([
                    z
                      .object({
                        code: z
                          .enum([
                            'aa',
                            'ab',
                            'ae',
                            'af',
                            'ak',
                            'am',
                            'an',
                            'ar',
                            'as',
                            'av',
                            'ay',
                            'az',
                            'ba',
                            'be',
                            'bg',
                            'bh',
                            'bi',
                            'bm',
                            'bn',
                            'bo',
                            'br',
                            'bs',
                            'ca',
                            'ce',
                            'ch',
                            'co',
                            'cr',
                            'cs',
                            'cu',
                            'cv',
                            'cy',
                            'da',
                            'de',
                            'dv',
                            'dz',
                            'ee',
                            'el',
                            'en',
                            'eo',
                            'es',
                            'et',
                            'eu',
                            'fa',
                            'ff',
                            'fi',
                            'fj',
                            'fo',
                            'fr',
                            'fy',
                            'ga',
                            'gd',
                            'gl',
                            'gn',
                            'gu',
                            'gv',
                            'ha',
                            'he',
                            'hi',
                            'ho',
                            'hr',
                            'ht',
                            'hu',
                            'hy',
                            'hz',
                            'ia',
                            'id',
                            'ie',
                            'ig',
                            'ii',
                            'ik',
                            'io',
                            'is',
                            'it',
                            'iu',
                            'ja',
                            'jv',
                            'ka',
                            'kg',
                            'ki',
                            'kj',
                            'kk',
                            'kl',
                            'km',
                            'kn',
                            'ko',
                            'kr',
                            'ks',
                            'ku',
                            'kv',
                            'kw',
                            'ky',
                            'la',
                            'lb',
                            'lg',
                            'li',
                            'ln',
                            'lo',
                            'lt',
                            'lu',
                            'lv',
                            'mg',
                            'mh',
                            'mi',
                            'mk',
                            'ml',
                            'mn',
                            'mr',
                            'ms',
                            'mt',
                            'my',
                            'na',
                            'nb',
                            'nd',
                            'ne',
                            'ng',
                            'nl',
                            'nn',
                            'no',
                            'nr',
                            'nv',
                            'ny',
                            'oc',
                            'oj',
                            'om',
                            'or',
                            'os',
                            'pa',
                            'pi',
                            'pl',
                            'ps',
                            'pt',
                            'qu',
                            'rm',
                            'rn',
                            'ro',
                            'ru',
                            'rw',
                            'sa',
                            'sc',
                            'sd',
                            'se',
                            'sg',
                            'sh',
                            'si',
                            'sk',
                            'sl',
                            'sm',
                            'sn',
                            'so',
                            'sq',
                            'sr',
                            'ss',
                            'st',
                            'su',
                            'sv',
                            'sw',
                            'ta',
                            'te',
                            'tg',
                            'th',
                            'ti',
                            'tk',
                            'tl',
                            'tn',
                            'to',
                            'tr',
                            'ts',
                            'tt',
                            'tw',
                            'ty',
                            'ug',
                            'uk',
                            'ur',
                            'uz',
                            've',
                            'vi',
                            'vo',
                            'wa',
                            'wo',
                            'xh',
                            'yi',
                            'yo',
                            'za',
                            'zh',
                            'zu',
                          ])
                          .describe(
                            'Two-letter human language primary subtags using BCP-47 values.',
                          ),
                        confidence: z
                          .union([z.number().gte(0).lte(1), z.null()])
                          .describe('The confidence of the prediction.')
                          .default(null),
                        created_by: z
                          .union([z.string(), z.null()])
                          .describe('The origin of the prediction.')
                          .default(null),
                      })
                      .catchall(z.any())
                      .describe('Detected human language.'),
                    z.null(),
                  ])
                  .default(null),
                summary: z
                  .union([
                    z
                      .object({
                        confidence: z
                          .union([z.number().gte(0).lte(1), z.null()])
                          .describe('The confidence of the prediction.')
                          .default(null),
                        created_by: z
                          .union([z.string(), z.null()])
                          .describe('The origin of the prediction.')
                          .default(null),
                        text: z.string(),
                      })
                      .catchall(z.any())
                      .describe('Summary data.'),
                    z.null(),
                  ])
                  .default(null),
              })
              .catchall(z.any())
              .describe('Base class for metadata.'),
            z.null(),
          ])
          .default(null),
        name: z.string().default('group'),
        parent: z
          .union([
            z
              .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
              .describe('RefItem.'),
            z.null(),
          ])
          .default(null),
        self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
      })
      .strict()
      .describe('GroupItem.')
      .default({
        children: [],
        content_layer: 'furniture',
        label: 'unspecified',
        meta: null,
        name: '_root_',
        parent: null,
        self_ref: '#/furniture',
      }),
    groups: z
      .array(
        z.union([
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              label: z.literal('list').default('list'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              name: z.string().default('group'),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            })
            .strict()
            .describe('ListGroup.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              label: z.literal('inline').default('inline'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              name: z.string().default('group'),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            })
            .strict()
            .describe('InlineGroup.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              label: z
                .enum([
                  'unspecified',
                  'list',
                  'ordered_list',
                  'chapter',
                  'section',
                  'sheet',
                  'slide',
                  'form_area',
                  'key_value_area',
                  'comment_section',
                  'inline',
                  'picture_area',
                ])
                .describe('GroupLabel.')
                .default('unspecified'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              name: z.string().default('group'),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            })
            .strict()
            .describe('GroupItem.'),
        ]),
      )
      .default([]),
    key_value_items: z
      .array(
        z
          .object({
            captions: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            footnotes: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            graph: z
              .object({
                cells: z
                  .array(
                    z
                      .object({
                        cell_id: z.number().int(),
                        item_ref: z
                          .union([
                            z
                              .object({
                                $ref: z
                                  .string()
                                  .regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                              })
                              .describe('RefItem.'),
                            z.null(),
                          ])
                          .default(null),
                        label: z
                          .enum(['unspecified', 'key', 'value', 'checkbox'])
                          .describe('GraphCellLabel.'),
                        orig: z.string(),
                        prov: z
                          .union([
                            z
                              .object({
                                bbox: z
                                  .object({
                                    b: z.number(),
                                    coord_origin: z
                                      .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                      .describe('CoordOrigin.')
                                      .default('TOPLEFT'),
                                    l: z.number(),
                                    r: z.number(),
                                    t: z.number(),
                                  })
                                  .describe('Bounding box'),
                                charspan: z
                                  .array(z.any())
                                  .min(2)
                                  .max(2)
                                  .describe('Character span (0-indexed)'),
                                page_no: z.number().int().describe('Page number'),
                              })
                              .describe(
                                'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                              ),
                            z.null(),
                          ])
                          .default(null),
                        text: z.string(),
                      })
                      .describe('GraphCell.'),
                  )
                  .optional(),
                links: z
                  .array(
                    z
                      .object({
                        label: z
                          .enum(['unspecified', 'to_value', 'to_key', 'to_parent', 'to_child'])
                          .describe('GraphLinkLabel.'),
                        source_cell_id: z.number().int(),
                        target_cell_id: z.number().int(),
                      })
                      .describe('GraphLink.'),
                  )
                  .optional(),
              })
              .describe('GraphData.'),
            image: z
              .union([
                z
                  .object({
                    dpi: z.number().int(),
                    mimetype: z.string(),
                    size: z
                      .object({ height: z.number().default(0), width: z.number().default(0) })
                      .describe('Size.'),
                    uri: z.union([z.string().url().min(1), z.string()]),
                  })
                  .describe('ImageRef.'),
                z.null(),
              ])
              .default(null),
            label: z.literal('key_value_region').default('key_value_region'),
            meta: z
              .union([
                z
                  .object({
                    description: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Description metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Metadata model for floating.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            references: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict()
          .describe('KeyValueItem.'),
      )
      .default([]),
    name: z.string(),
    origin: z
      .union([
        z
          .object({
            binary_hash: z.number().int().gte(0).lte(18446744073709552000),
            filename: z.string(),
            mimetype: z.string(),
            uri: z.union([z.string().url().min(1), z.null()]).default(null),
          })
          .describe('FileSource.'),
        z.null(),
      ])
      .default(null),
    pages: z
      .record(
        z.string(),
        z
          .object({
            image: z
              .union([
                z
                  .object({
                    dpi: z.number().int(),
                    mimetype: z.string(),
                    size: z
                      .object({ height: z.number().default(0), width: z.number().default(0) })
                      .describe('Size.'),
                    uri: z.union([z.string().url().min(1), z.string()]),
                  })
                  .describe('ImageRef.'),
                z.null(),
              ])
              .default(null),
            page_no: z.number().int(),
            size: z
              .object({ height: z.number().default(0), width: z.number().default(0) })
              .describe('Size.'),
          })
          .describe('PageItem.'),
      )
      .default({}),
    pictures: z
      .array(
        z
          .object({
            annotations: z
              .array(
                z.any().superRefine((x, ctx) => {
                  const schemas = [
                    z
                      .object({
                        kind: z.literal('description').default('description'),
                        provenance: z.string(),
                        text: z.string(),
                      })
                      .describe('DescriptionAnnotation.'),
                    z
                      .object({
                        content: z.record(z.string(), z.any()),
                        kind: z.literal('misc').default('misc'),
                      })
                      .describe('MiscAnnotation.'),
                    z
                      .object({
                        kind: z.literal('classification').default('classification'),
                        predicted_classes: z.array(
                          z
                            .object({ class_name: z.string(), confidence: z.number() })
                            .describe('PictureClassificationData.'),
                        ),
                        provenance: z.string(),
                      })
                      .describe('PictureClassificationData.'),
                    z
                      .object({
                        class_name: z.string(),
                        confidence: z.number(),
                        kind: z.literal('molecule_data').default('molecule_data'),
                        provenance: z.string(),
                        segmentation: z.array(z.array(z.any()).min(2).max(2)),
                        smi: z.string(),
                      })
                      .describe('PictureMoleculeData.'),
                    z
                      .object({
                        chart_data: z
                          .object({
                            num_cols: z.number().int().default(0),
                            num_rows: z.number().int().default(0),
                            table_cells: z
                              .array(
                                z.union([
                                  z
                                    .object({
                                      bbox: z
                                        .union([
                                          z
                                            .object({
                                              b: z.number(),
                                              coord_origin: z
                                                .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                                .describe('CoordOrigin.')
                                                .default('TOPLEFT'),
                                              l: z.number(),
                                              r: z.number(),
                                              t: z.number(),
                                            })
                                            .describe('BoundingBox.'),
                                          z.null(),
                                        ])
                                        .default(null),
                                      col_span: z.number().int().default(1),
                                      column_header: z.boolean().default(false),
                                      end_col_offset_idx: z.number().int(),
                                      end_row_offset_idx: z.number().int(),
                                      fillable: z.boolean().default(false),
                                      ref: z
                                        .object({
                                          $ref: z
                                            .string()
                                            .regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                                        })
                                        .describe('RefItem.'),
                                      row_header: z.boolean().default(false),
                                      row_section: z.boolean().default(false),
                                      row_span: z.number().int().default(1),
                                      start_col_offset_idx: z.number().int(),
                                      start_row_offset_idx: z.number().int(),
                                      text: z.string(),
                                    })
                                    .describe('RichTableCell.'),
                                  z
                                    .object({
                                      bbox: z
                                        .union([
                                          z
                                            .object({
                                              b: z.number(),
                                              coord_origin: z
                                                .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                                .describe('CoordOrigin.')
                                                .default('TOPLEFT'),
                                              l: z.number(),
                                              r: z.number(),
                                              t: z.number(),
                                            })
                                            .describe('BoundingBox.'),
                                          z.null(),
                                        ])
                                        .default(null),
                                      col_span: z.number().int().default(1),
                                      column_header: z.boolean().default(false),
                                      end_col_offset_idx: z.number().int(),
                                      end_row_offset_idx: z.number().int(),
                                      fillable: z.boolean().default(false),
                                      row_header: z.boolean().default(false),
                                      row_section: z.boolean().default(false),
                                      row_span: z.number().int().default(1),
                                      start_col_offset_idx: z.number().int(),
                                      start_row_offset_idx: z.number().int(),
                                      text: z.string(),
                                    })
                                    .describe('TableCell.'),
                                ]),
                              )
                              .default([]),
                          })
                          .describe('BaseTableData.'),
                        kind: z.literal('tabular_chart_data').default('tabular_chart_data'),
                        title: z.string(),
                      })
                      .describe(
                        'Base class for picture chart data.\n\nAttributes:\n    title (str): The title of the chart.\n    chart_data (TableData): Chart data in the table format.',
                      ),
                    z
                      .object({
                        kind: z.literal('line_chart_data').default('line_chart_data'),
                        lines: z.array(
                          z
                            .object({
                              label: z.string(),
                              values: z.array(z.array(z.any()).min(2).max(2)),
                            })
                            .describe(
                              "Represents a line in a line chart.\n\nAttributes:\n    label (str): The label for the line.\n    values (list[tuple[float, float]]): A list of (x, y) coordinate pairs\n        representing the line's data points.",
                            ),
                        ),
                        title: z.string(),
                        x_axis_label: z.string(),
                        y_axis_label: z.string(),
                      })
                      .describe(
                        'Represents data of a line chart.\n\nAttributes:\n    kind (Literal["line_chart_data"]): The type of the chart.\n    x_axis_label (str): The label for the x-axis.\n    y_axis_label (str): The label for the y-axis.\n    lines (list[ChartLine]): A list of lines in the chart.',
                      ),
                    z
                      .object({
                        bars: z.array(
                          z
                            .object({ label: z.string(), values: z.number() })
                            .describe(
                              'Represents a bar in a bar chart.\n\nAttributes:\n    label (str): The label for the bar.\n    values (float): The value associated with the bar.',
                            ),
                        ),
                        kind: z.literal('bar_chart_data').default('bar_chart_data'),
                        title: z.string(),
                        x_axis_label: z.string(),
                        y_axis_label: z.string(),
                      })
                      .describe(
                        'Represents data of a bar chart.\n\nAttributes:\n    kind (Literal["bar_chart_data"]): The type of the chart.\n    x_axis_label (str): The label for the x-axis.\n    y_axis_label (str): The label for the y-axis.\n    bars (list[ChartBar]): A list of bars in the chart.',
                      ),
                    z
                      .object({
                        kind: z.literal('stacked_bar_chart_data').default('stacked_bar_chart_data'),
                        stacked_bars: z.array(
                          z
                            .object({
                              label: z.array(z.string()),
                              values: z.array(z.array(z.any()).min(2).max(2)),
                            })
                            .describe(
                              'Represents a stacked bar in a stacked bar chart.\n\nAttributes:\n    label (list[str]): The labels for the stacked bars. Multiple values are stored\n        in cases where the chart is "double stacked," meaning bars are stacked both\n        horizontally and vertically.\n    values (list[tuple[str, int]]): A list of values representing different segments\n        of the stacked bar along with their label.',
                            ),
                        ),
                        title: z.string(),
                        x_axis_label: z.string(),
                        y_axis_label: z.string(),
                      })
                      .describe(
                        'Represents data of a stacked bar chart.\n\nAttributes:\n    kind (Literal["stacked_bar_chart_data"]): The type of the chart.\n    x_axis_label (str): The label for the x-axis.\n    y_axis_label (str): The label for the y-axis.\n    stacked_bars (list[ChartStackedBar]): A list of stacked bars in the chart.',
                      ),
                    z
                      .object({
                        kind: z.literal('pie_chart_data').default('pie_chart_data'),
                        slices: z.array(
                          z
                            .object({ label: z.string(), value: z.number() })
                            .describe(
                              'Represents a slice in a pie chart.\n\nAttributes:\n    label (str): The label for the slice.\n    value (float): The value represented by the slice.',
                            ),
                        ),
                        title: z.string(),
                      })
                      .describe(
                        'Represents data of a pie chart.\n\nAttributes:\n    kind (Literal["pie_chart_data"]): The type of the chart.\n    slices (list[ChartSlice]): A list of slices in the pie chart.',
                      ),
                    z
                      .object({
                        kind: z.literal('scatter_chart_data').default('scatter_chart_data'),
                        points: z.array(
                          z
                            .object({ value: z.array(z.any()).min(2).max(2) })
                            .describe(
                              'Represents a point in a scatter chart.\n\nAttributes:\n    value (Tuple[float, float]): A (x, y) coordinate pair representing a point in a\n        chart.',
                            ),
                        ),
                        title: z.string(),
                        x_axis_label: z.string(),
                        y_axis_label: z.string(),
                      })
                      .describe(
                        'Represents data of a scatter chart.\n\nAttributes:\n    kind (Literal["scatter_chart_data"]): The type of the chart.\n    x_axis_label (str): The label for the x-axis.\n    y_axis_label (str): The label for the y-axis.\n    points (list[ChartPoint]): A list of points in the scatter chart.',
                      ),
                  ]
                  const { errors, failed } = schemas.reduce<{
                    errors: z.core.$ZodIssue[]
                    failed: number
                  }>(
                    ({ errors, failed }, schema) =>
                      ((result) =>
                        result.error
                          ? {
                              errors: [...errors, ...result.error.issues],
                              failed: failed + 1,
                            }
                          : { errors, failed })(schema.safeParse(x)),
                    { errors: [], failed: 0 },
                  )
                  const passed = schemas.length - failed
                  if (passed !== 1) {
                    ctx.addIssue(
                      errors.length
                        ? {
                            path: [],
                            code: 'invalid_union',
                            errors: [errors],
                            message: 'Invalid input: Should pass single schema. Passed ' + passed,
                          }
                        : {
                            path: [],
                            code: 'custom',
                            errors: [errors],
                            message: 'Invalid input: Should pass single schema. Passed ' + passed,
                          },
                    )
                  }
                }),
              )
              .default([]),
            captions: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            footnotes: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            image: z
              .union([
                z
                  .object({
                    dpi: z.number().int(),
                    mimetype: z.string(),
                    size: z
                      .object({ height: z.number().default(0), width: z.number().default(0) })
                      .describe('Size.'),
                    uri: z.union([z.string().url().min(1), z.string()]),
                  })
                  .describe('ImageRef.'),
                z.null(),
              ])
              .default(null),
            label: z.enum(['picture', 'chart']).default('picture'),
            meta: z
              .union([
                z
                  .object({
                    classification: z
                      .union([
                        z
                          .object({
                            predictions: z
                              .array(
                                z
                                  .object({
                                    class_name: z.string(),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                  })
                                  .catchall(z.any())
                                  .describe('Picture classification instance.'),
                              )
                              .min(1)
                              .optional(),
                          })
                          .catchall(z.any())
                          .describe('Picture classification metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    code: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            language: z
                              .union([
                                z
                                  .enum([
                                    'Ada',
                                    'Awk',
                                    'Bash',
                                    'bc',
                                    'C',
                                    'C#',
                                    'C++',
                                    'CMake',
                                    'COBOL',
                                    'CSS',
                                    'Ceylon',
                                    'Clojure',
                                    'Crystal',
                                    'Cuda',
                                    'Cython',
                                    'D',
                                    'Dart',
                                    'dc',
                                    'Dockerfile',
                                    'DocLang',
                                    'Elixir',
                                    'Erlang',
                                    'FORTRAN',
                                    'Forth',
                                    'Go',
                                    'HTML',
                                    'Haskell',
                                    'Haxe',
                                    'Java',
                                    'JavaScript',
                                    'JSON',
                                    'Julia',
                                    'Kotlin',
                                    'Latex',
                                    'Lisp',
                                    'Lua',
                                    'Matlab',
                                    'MoonScript',
                                    'Nim',
                                    'OCaml',
                                    'ObjectiveC',
                                    'Octave',
                                    'PHP',
                                    'Pascal',
                                    'Perl',
                                    'Prolog',
                                    'Python',
                                    'Racket',
                                    'Ruby',
                                    'Rust',
                                    'SML',
                                    'SQL',
                                    'Scala',
                                    'Scheme',
                                    'Swift',
                                    'Tikz',
                                    'TypeScript',
                                    'unknown',
                                    'VisualBasic',
                                    'XML',
                                    'YAML',
                                  ])
                                  .describe('CodeLanguageLabel.'),
                                z.null(),
                              ])
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Code representation for the respective item.'),
                        z.null(),
                      ])
                      .default(null),
                    description: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Description metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    molecule: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            smi: z.string().describe('The SMILES representation of the molecule.'),
                          })
                          .catchall(z.any())
                          .describe('Molecule metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                    tabular_chart: z
                      .union([
                        z
                          .object({
                            chart_data: z
                              .object({
                                num_cols: z.number().int().default(0),
                                num_rows: z.number().int().default(0),
                                table_cells: z
                                  .array(
                                    z.union([
                                      z
                                        .object({
                                          bbox: z
                                            .union([
                                              z
                                                .object({
                                                  b: z.number(),
                                                  coord_origin: z
                                                    .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                                    .describe('CoordOrigin.')
                                                    .default('TOPLEFT'),
                                                  l: z.number(),
                                                  r: z.number(),
                                                  t: z.number(),
                                                })
                                                .describe('BoundingBox.'),
                                              z.null(),
                                            ])
                                            .default(null),
                                          col_span: z.number().int().default(1),
                                          column_header: z.boolean().default(false),
                                          end_col_offset_idx: z.number().int(),
                                          end_row_offset_idx: z.number().int(),
                                          fillable: z.boolean().default(false),
                                          ref: z
                                            .object({
                                              $ref: z
                                                .string()
                                                .regex(
                                                  new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$'),
                                                ),
                                            })
                                            .describe('RefItem.'),
                                          row_header: z.boolean().default(false),
                                          row_section: z.boolean().default(false),
                                          row_span: z.number().int().default(1),
                                          start_col_offset_idx: z.number().int(),
                                          start_row_offset_idx: z.number().int(),
                                          text: z.string(),
                                        })
                                        .describe('RichTableCell.'),
                                      z
                                        .object({
                                          bbox: z
                                            .union([
                                              z
                                                .object({
                                                  b: z.number(),
                                                  coord_origin: z
                                                    .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                                    .describe('CoordOrigin.')
                                                    .default('TOPLEFT'),
                                                  l: z.number(),
                                                  r: z.number(),
                                                  t: z.number(),
                                                })
                                                .describe('BoundingBox.'),
                                              z.null(),
                                            ])
                                            .default(null),
                                          col_span: z.number().int().default(1),
                                          column_header: z.boolean().default(false),
                                          end_col_offset_idx: z.number().int(),
                                          end_row_offset_idx: z.number().int(),
                                          fillable: z.boolean().default(false),
                                          row_header: z.boolean().default(false),
                                          row_section: z.boolean().default(false),
                                          row_span: z.number().int().default(1),
                                          start_col_offset_idx: z.number().int(),
                                          start_row_offset_idx: z.number().int(),
                                          text: z.string(),
                                        })
                                        .describe('TableCell.'),
                                    ]),
                                  )
                                  .default([]),
                              })
                              .describe('BaseTableData.'),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            title: z.union([z.string(), z.null()]).default(null),
                          })
                          .catchall(z.any())
                          .describe('Tabular chart metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Metadata model for pictures.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            references: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict()
          .describe('PictureItem.'),
      )
      .default([]),
    schema_name: z.literal('DoclingDocument').default('DoclingDocument'),
    tables: z
      .array(
        z
          .object({
            annotations: z
              .array(
                z.any().superRefine((x, ctx) => {
                  const schemas = [
                    z
                      .object({
                        kind: z.literal('description').default('description'),
                        provenance: z.string(),
                        text: z.string(),
                      })
                      .describe('DescriptionAnnotation.'),
                    z
                      .object({
                        content: z.record(z.string(), z.any()),
                        kind: z.literal('misc').default('misc'),
                      })
                      .describe('MiscAnnotation.'),
                  ]
                  const { errors, failed } = schemas.reduce<{
                    errors: z.core.$ZodIssue[]
                    failed: number
                  }>(
                    ({ errors, failed }, schema) =>
                      ((result) =>
                        result.error
                          ? {
                              errors: [...errors, ...result.error.issues],
                              failed: failed + 1,
                            }
                          : { errors, failed })(schema.safeParse(x)),
                    { errors: [], failed: 0 },
                  )
                  const passed = schemas.length - failed
                  if (passed !== 1) {
                    ctx.addIssue(
                      errors.length
                        ? {
                            path: [],
                            code: 'invalid_union',
                            errors: [errors],
                            message: 'Invalid input: Should pass single schema. Passed ' + passed,
                          }
                        : {
                            path: [],
                            code: 'custom',
                            errors: [errors],
                            message: 'Invalid input: Should pass single schema. Passed ' + passed,
                          },
                    )
                  }
                }),
              )
              .default([]),
            captions: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            children: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            comments: z
              .array(
                z
                  .object({
                    $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                  })
                  .describe('Fine-granular reference item that can capture span range info.'),
              )
              .default([]),
            content_layer: z
              .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
              .describe('ContentLayer.')
              .default('body'),
            data: z
              .object({
                num_cols: z.number().int().default(0),
                num_rows: z.number().int().default(0),
                table_cells: z
                  .array(
                    z.union([
                      z
                        .object({
                          bbox: z
                            .union([
                              z
                                .object({
                                  b: z.number(),
                                  coord_origin: z
                                    .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                    .describe('CoordOrigin.')
                                    .default('TOPLEFT'),
                                  l: z.number(),
                                  r: z.number(),
                                  t: z.number(),
                                })
                                .describe('BoundingBox.'),
                              z.null(),
                            ])
                            .default(null),
                          col_span: z.number().int().default(1),
                          column_header: z.boolean().default(false),
                          end_col_offset_idx: z.number().int(),
                          end_row_offset_idx: z.number().int(),
                          fillable: z.boolean().default(false),
                          ref: z
                            .object({
                              $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                            })
                            .describe('RefItem.'),
                          row_header: z.boolean().default(false),
                          row_section: z.boolean().default(false),
                          row_span: z.number().int().default(1),
                          start_col_offset_idx: z.number().int(),
                          start_row_offset_idx: z.number().int(),
                          text: z.string(),
                        })
                        .describe('RichTableCell.'),
                      z
                        .object({
                          bbox: z
                            .union([
                              z
                                .object({
                                  b: z.number(),
                                  coord_origin: z
                                    .enum(['TOPLEFT', 'BOTTOMLEFT'])
                                    .describe('CoordOrigin.')
                                    .default('TOPLEFT'),
                                  l: z.number(),
                                  r: z.number(),
                                  t: z.number(),
                                })
                                .describe('BoundingBox.'),
                              z.null(),
                            ])
                            .default(null),
                          col_span: z.number().int().default(1),
                          column_header: z.boolean().default(false),
                          end_col_offset_idx: z.number().int(),
                          end_row_offset_idx: z.number().int(),
                          fillable: z.boolean().default(false),
                          row_header: z.boolean().default(false),
                          row_section: z.boolean().default(false),
                          row_span: z.number().int().default(1),
                          start_col_offset_idx: z.number().int(),
                          start_row_offset_idx: z.number().int(),
                          text: z.string(),
                        })
                        .describe('TableCell.'),
                    ]),
                  )
                  .default([]),
              })
              .describe('BaseTableData.'),
            footnotes: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            image: z
              .union([
                z
                  .object({
                    dpi: z.number().int(),
                    mimetype: z.string(),
                    size: z
                      .object({ height: z.number().default(0), width: z.number().default(0) })
                      .describe('Size.'),
                    uri: z.union([z.string().url().min(1), z.string()]),
                  })
                  .describe('ImageRef.'),
                z.null(),
              ])
              .default(null),
            label: z.enum(['document_index', 'table']).default('table'),
            meta: z
              .union([
                z
                  .object({
                    description: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Description metadata field.'),
                        z.null(),
                      ])
                      .default(null),
                    entities: z
                      .union([
                        z
                          .object({
                            mentions: z
                              .array(
                                z
                                  .object({
                                    charspan: z
                                      .union([
                                        z
                                          .array(z.any())
                                          .min(2)
                                          .max(2)
                                          .describe('Character span (0-indexed)'),
                                        z.null(),
                                      ])
                                      .describe(
                                        'Character span (0-indexed) of the entity mention in the source text.',
                                      )
                                      .default(null),
                                    confidence: z
                                      .union([z.number().gte(0).lte(1), z.null()])
                                      .describe('The confidence of the prediction.')
                                      .default(null),
                                    created_by: z
                                      .union([z.string(), z.null()])
                                      .describe('The origin of the prediction.')
                                      .default(null),
                                    label: z
                                      .union([z.string(), z.null()])
                                      .describe('Entity type or category.')
                                      .default(null),
                                    orig: z
                                      .union([z.string(), z.null()])
                                      .describe(
                                        "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                      )
                                      .default(null),
                                    text: z
                                      .string()
                                      .describe('Normalized text of the entity mention.'),
                                  })
                                  .catchall(z.any())
                                  .describe('Entity mention extracted from text.'),
                              )
                              .min(1),
                          })
                          .catchall(z.any())
                          .describe('Container for extracted entity mentions.'),
                        z.null(),
                      ])
                      .default(null),
                    language: z
                      .union([
                        z
                          .object({
                            code: z
                              .enum([
                                'aa',
                                'ab',
                                'ae',
                                'af',
                                'ak',
                                'am',
                                'an',
                                'ar',
                                'as',
                                'av',
                                'ay',
                                'az',
                                'ba',
                                'be',
                                'bg',
                                'bh',
                                'bi',
                                'bm',
                                'bn',
                                'bo',
                                'br',
                                'bs',
                                'ca',
                                'ce',
                                'ch',
                                'co',
                                'cr',
                                'cs',
                                'cu',
                                'cv',
                                'cy',
                                'da',
                                'de',
                                'dv',
                                'dz',
                                'ee',
                                'el',
                                'en',
                                'eo',
                                'es',
                                'et',
                                'eu',
                                'fa',
                                'ff',
                                'fi',
                                'fj',
                                'fo',
                                'fr',
                                'fy',
                                'ga',
                                'gd',
                                'gl',
                                'gn',
                                'gu',
                                'gv',
                                'ha',
                                'he',
                                'hi',
                                'ho',
                                'hr',
                                'ht',
                                'hu',
                                'hy',
                                'hz',
                                'ia',
                                'id',
                                'ie',
                                'ig',
                                'ii',
                                'ik',
                                'io',
                                'is',
                                'it',
                                'iu',
                                'ja',
                                'jv',
                                'ka',
                                'kg',
                                'ki',
                                'kj',
                                'kk',
                                'kl',
                                'km',
                                'kn',
                                'ko',
                                'kr',
                                'ks',
                                'ku',
                                'kv',
                                'kw',
                                'ky',
                                'la',
                                'lb',
                                'lg',
                                'li',
                                'ln',
                                'lo',
                                'lt',
                                'lu',
                                'lv',
                                'mg',
                                'mh',
                                'mi',
                                'mk',
                                'ml',
                                'mn',
                                'mr',
                                'ms',
                                'mt',
                                'my',
                                'na',
                                'nb',
                                'nd',
                                'ne',
                                'ng',
                                'nl',
                                'nn',
                                'no',
                                'nr',
                                'nv',
                                'ny',
                                'oc',
                                'oj',
                                'om',
                                'or',
                                'os',
                                'pa',
                                'pi',
                                'pl',
                                'ps',
                                'pt',
                                'qu',
                                'rm',
                                'rn',
                                'ro',
                                'ru',
                                'rw',
                                'sa',
                                'sc',
                                'sd',
                                'se',
                                'sg',
                                'sh',
                                'si',
                                'sk',
                                'sl',
                                'sm',
                                'sn',
                                'so',
                                'sq',
                                'sr',
                                'ss',
                                'st',
                                'su',
                                'sv',
                                'sw',
                                'ta',
                                'te',
                                'tg',
                                'th',
                                'ti',
                                'tk',
                                'tl',
                                'tn',
                                'to',
                                'tr',
                                'ts',
                                'tt',
                                'tw',
                                'ty',
                                'ug',
                                'uk',
                                'ur',
                                'uz',
                                've',
                                'vi',
                                'vo',
                                'wa',
                                'wo',
                                'xh',
                                'yi',
                                'yo',
                                'za',
                                'zh',
                                'zu',
                              ])
                              .describe(
                                'Two-letter human language primary subtags using BCP-47 values.',
                              ),
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                          })
                          .catchall(z.any())
                          .describe('Detected human language.'),
                        z.null(),
                      ])
                      .default(null),
                    summary: z
                      .union([
                        z
                          .object({
                            confidence: z
                              .union([z.number().gte(0).lte(1), z.null()])
                              .describe('The confidence of the prediction.')
                              .default(null),
                            created_by: z
                              .union([z.string(), z.null()])
                              .describe('The origin of the prediction.')
                              .default(null),
                            text: z.string(),
                          })
                          .catchall(z.any())
                          .describe('Summary data.'),
                        z.null(),
                      ])
                      .default(null),
                  })
                  .catchall(z.any())
                  .describe('Metadata model for floating.'),
                z.null(),
              ])
              .default(null),
            parent: z
              .union([
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
                z.null(),
              ])
              .default(null),
            prov: z
              .array(
                z
                  .object({
                    bbox: z
                      .object({
                        b: z.number(),
                        coord_origin: z
                          .enum(['TOPLEFT', 'BOTTOMLEFT'])
                          .describe('CoordOrigin.')
                          .default('TOPLEFT'),
                        l: z.number(),
                        r: z.number(),
                        t: z.number(),
                      })
                      .describe('Bounding box'),
                    charspan: z.array(z.any()).min(2).max(2).describe('Character span (0-indexed)'),
                    page_no: z.number().int().describe('Page number'),
                  })
                  .describe(
                    'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                  ),
              )
              .default([]),
            references: z
              .array(
                z
                  .object({ $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')) })
                  .describe('RefItem.'),
              )
              .default([]),
            self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
            source: z
              .array(
                z
                  .object({
                    end_time: z.number().describe('End time offset of the track cue in seconds'),
                    identifier: z
                      .union([z.string(), z.null()])
                      .describe('An identifier of the cue')
                      .default(null),
                    kind: z
                      .literal('track')
                      .describe('Identifies this type of source.')
                      .default('track'),
                    start_time: z
                      .number()
                      .describe('Start time offset of the track cue in seconds'),
                    voice: z
                      .union([z.string(), z.null()])
                      .describe('The name of the voice in this track (the speaker)')
                      .default(null),
                  })
                  .describe(
                    'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                  ),
              )
              .describe(
                'The provenance of this document item. Currently, it is only used for media track provenance.',
              )
              .default([]),
          })
          .strict()
          .describe('TableItem.'),
      )
      .default([]),
    texts: z
      .array(
        z.union([
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.literal('title').default('title'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('TitleItem.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.literal('section_header').default('section_header'),
              level: z.number().int().gte(1).lte(100).default(1),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('SectionItem.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              enumerated: z.boolean().default(false),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.literal('list_item').default('list_item'),
              marker: z.string().default('-'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('SectionItem.'),
          z
            .object({
              captions: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              code_language: z
                .enum([
                  'Ada',
                  'Awk',
                  'Bash',
                  'bc',
                  'C',
                  'C#',
                  'C++',
                  'CMake',
                  'COBOL',
                  'CSS',
                  'Ceylon',
                  'Clojure',
                  'Crystal',
                  'Cuda',
                  'Cython',
                  'D',
                  'Dart',
                  'dc',
                  'Dockerfile',
                  'DocLang',
                  'Elixir',
                  'Erlang',
                  'FORTRAN',
                  'Forth',
                  'Go',
                  'HTML',
                  'Haskell',
                  'Haxe',
                  'Java',
                  'JavaScript',
                  'JSON',
                  'Julia',
                  'Kotlin',
                  'Latex',
                  'Lisp',
                  'Lua',
                  'Matlab',
                  'MoonScript',
                  'Nim',
                  'OCaml',
                  'ObjectiveC',
                  'Octave',
                  'PHP',
                  'Pascal',
                  'Perl',
                  'Prolog',
                  'Python',
                  'Racket',
                  'Ruby',
                  'Rust',
                  'SML',
                  'SQL',
                  'Scala',
                  'Scheme',
                  'Swift',
                  'Tikz',
                  'TypeScript',
                  'unknown',
                  'VisualBasic',
                  'XML',
                  'YAML',
                ])
                .describe('CodeLanguageLabel.')
                .default('unknown'),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              footnotes: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              image: z
                .union([
                  z
                    .object({
                      dpi: z.number().int(),
                      mimetype: z.string(),
                      size: z
                        .object({ height: z.number().default(0), width: z.number().default(0) })
                        .describe('Size.'),
                      uri: z.union([z.string().url().min(1), z.string()]),
                    })
                    .describe('ImageRef.'),
                  z.null(),
                ])
                .default(null),
              label: z.literal('code').default('code'),
              meta: z
                .union([
                  z
                    .object({
                      description: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Description metadata field.'),
                          z.null(),
                        ])
                        .default(null),
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Metadata model for floating.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              references: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('CodeItem.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.literal('formula').default('formula'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('FormulaItem.'),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.literal('field_heading').default('field_heading'),
              level: z.number().int().gte(1).lte(100).default(1),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict(),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              kind: z.enum(['read_only', 'fillable']).default('read_only'),
              label: z.literal('field_value').default('field_value'),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict(),
          z
            .object({
              children: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                )
                .default([]),
              comments: z
                .array(
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                      range: z.union([z.array(z.any()).min(2).max(2), z.null()]).default(null),
                    })
                    .describe('Fine-granular reference item that can capture span range info.'),
                )
                .default([]),
              content_layer: z
                .enum(['body', 'furniture', 'background', 'invisible', 'notes'])
                .describe('ContentLayer.')
                .default('body'),
              formatting: z
                .union([
                  z
                    .object({
                      bold: z.boolean().default(false),
                      italic: z.boolean().default(false),
                      script: z
                        .enum(['baseline', 'sub', 'super'])
                        .describe('Text script position.')
                        .default('baseline'),
                      strikethrough: z.boolean().default(false),
                      underline: z.boolean().default(false),
                    })
                    .describe('Formatting.'),
                  z.null(),
                ])
                .default(null),
              hyperlink: z.union([z.string().url().min(1), z.string(), z.null()]).default(null),
              label: z.enum([
                'caption',
                'checkbox_selected',
                'checkbox_unselected',
                'footnote',
                'page_footer',
                'page_header',
                'paragraph',
                'reference',
                'text',
                'empty_value',
                'field_key',
                'field_hint',
                'marker',
                'handwritten_text',
              ]),
              meta: z
                .union([
                  z
                    .object({
                      entities: z
                        .union([
                          z
                            .object({
                              mentions: z
                                .array(
                                  z
                                    .object({
                                      charspan: z
                                        .union([
                                          z
                                            .array(z.any())
                                            .min(2)
                                            .max(2)
                                            .describe('Character span (0-indexed)'),
                                          z.null(),
                                        ])
                                        .describe(
                                          'Character span (0-indexed) of the entity mention in the source text.',
                                        )
                                        .default(null),
                                      confidence: z
                                        .union([z.number().gte(0).lte(1), z.null()])
                                        .describe('The confidence of the prediction.')
                                        .default(null),
                                      created_by: z
                                        .union([z.string(), z.null()])
                                        .describe('The origin of the prediction.')
                                        .default(null),
                                      label: z
                                        .union([z.string(), z.null()])
                                        .describe('Entity type or category.')
                                        .default(null),
                                      orig: z
                                        .union([z.string(), z.null()])
                                        .describe(
                                          "Exact source text extracted from the original charspan, analogous to TextItem.orig. This may differ from 'text' when the mention has been normalized.",
                                        )
                                        .default(null),
                                      text: z
                                        .string()
                                        .describe('Normalized text of the entity mention.'),
                                    })
                                    .catchall(z.any())
                                    .describe('Entity mention extracted from text.'),
                                )
                                .min(1),
                            })
                            .catchall(z.any())
                            .describe('Container for extracted entity mentions.'),
                          z.null(),
                        ])
                        .default(null),
                      language: z
                        .union([
                          z
                            .object({
                              code: z
                                .enum([
                                  'aa',
                                  'ab',
                                  'ae',
                                  'af',
                                  'ak',
                                  'am',
                                  'an',
                                  'ar',
                                  'as',
                                  'av',
                                  'ay',
                                  'az',
                                  'ba',
                                  'be',
                                  'bg',
                                  'bh',
                                  'bi',
                                  'bm',
                                  'bn',
                                  'bo',
                                  'br',
                                  'bs',
                                  'ca',
                                  'ce',
                                  'ch',
                                  'co',
                                  'cr',
                                  'cs',
                                  'cu',
                                  'cv',
                                  'cy',
                                  'da',
                                  'de',
                                  'dv',
                                  'dz',
                                  'ee',
                                  'el',
                                  'en',
                                  'eo',
                                  'es',
                                  'et',
                                  'eu',
                                  'fa',
                                  'ff',
                                  'fi',
                                  'fj',
                                  'fo',
                                  'fr',
                                  'fy',
                                  'ga',
                                  'gd',
                                  'gl',
                                  'gn',
                                  'gu',
                                  'gv',
                                  'ha',
                                  'he',
                                  'hi',
                                  'ho',
                                  'hr',
                                  'ht',
                                  'hu',
                                  'hy',
                                  'hz',
                                  'ia',
                                  'id',
                                  'ie',
                                  'ig',
                                  'ii',
                                  'ik',
                                  'io',
                                  'is',
                                  'it',
                                  'iu',
                                  'ja',
                                  'jv',
                                  'ka',
                                  'kg',
                                  'ki',
                                  'kj',
                                  'kk',
                                  'kl',
                                  'km',
                                  'kn',
                                  'ko',
                                  'kr',
                                  'ks',
                                  'ku',
                                  'kv',
                                  'kw',
                                  'ky',
                                  'la',
                                  'lb',
                                  'lg',
                                  'li',
                                  'ln',
                                  'lo',
                                  'lt',
                                  'lu',
                                  'lv',
                                  'mg',
                                  'mh',
                                  'mi',
                                  'mk',
                                  'ml',
                                  'mn',
                                  'mr',
                                  'ms',
                                  'mt',
                                  'my',
                                  'na',
                                  'nb',
                                  'nd',
                                  'ne',
                                  'ng',
                                  'nl',
                                  'nn',
                                  'no',
                                  'nr',
                                  'nv',
                                  'ny',
                                  'oc',
                                  'oj',
                                  'om',
                                  'or',
                                  'os',
                                  'pa',
                                  'pi',
                                  'pl',
                                  'ps',
                                  'pt',
                                  'qu',
                                  'rm',
                                  'rn',
                                  'ro',
                                  'ru',
                                  'rw',
                                  'sa',
                                  'sc',
                                  'sd',
                                  'se',
                                  'sg',
                                  'sh',
                                  'si',
                                  'sk',
                                  'sl',
                                  'sm',
                                  'sn',
                                  'so',
                                  'sq',
                                  'sr',
                                  'ss',
                                  'st',
                                  'su',
                                  'sv',
                                  'sw',
                                  'ta',
                                  'te',
                                  'tg',
                                  'th',
                                  'ti',
                                  'tk',
                                  'tl',
                                  'tn',
                                  'to',
                                  'tr',
                                  'ts',
                                  'tt',
                                  'tw',
                                  'ty',
                                  'ug',
                                  'uk',
                                  'ur',
                                  'uz',
                                  've',
                                  'vi',
                                  'vo',
                                  'wa',
                                  'wo',
                                  'xh',
                                  'yi',
                                  'yo',
                                  'za',
                                  'zh',
                                  'zu',
                                ])
                                .describe(
                                  'Two-letter human language primary subtags using BCP-47 values.',
                                ),
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                            })
                            .catchall(z.any())
                            .describe('Detected human language.'),
                          z.null(),
                        ])
                        .default(null),
                      summary: z
                        .union([
                          z
                            .object({
                              confidence: z
                                .union([z.number().gte(0).lte(1), z.null()])
                                .describe('The confidence of the prediction.')
                                .default(null),
                              created_by: z
                                .union([z.string(), z.null()])
                                .describe('The origin of the prediction.')
                                .default(null),
                              text: z.string(),
                            })
                            .catchall(z.any())
                            .describe('Summary data.'),
                          z.null(),
                        ])
                        .default(null),
                    })
                    .catchall(z.any())
                    .describe('Base class for metadata.'),
                  z.null(),
                ])
                .default(null),
              orig: z.string(),
              parent: z
                .union([
                  z
                    .object({
                      $ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
                    })
                    .describe('RefItem.'),
                  z.null(),
                ])
                .default(null),
              prov: z
                .array(
                  z
                    .object({
                      bbox: z
                        .object({
                          b: z.number(),
                          coord_origin: z
                            .enum(['TOPLEFT', 'BOTTOMLEFT'])
                            .describe('CoordOrigin.')
                            .default('TOPLEFT'),
                          l: z.number(),
                          r: z.number(),
                          t: z.number(),
                        })
                        .describe('Bounding box'),
                      charspan: z
                        .array(z.any())
                        .min(2)
                        .max(2)
                        .describe('Character span (0-indexed)'),
                      page_no: z.number().int().describe('Page number'),
                    })
                    .describe(
                      'Provenance information for elements extracted from a textual document.\n\nA `ProvenanceItem` object acts as a lightweight pointer back into the original\ndocument for an extracted element. It applies to documents with an explicity\nor implicit layout, such as PDF, HTML, docx, or pptx.',
                    ),
                )
                .default([]),
              self_ref: z.string().regex(new RegExp('^#(?:/([\\w-]+)(?:/(\\d+))?)?$')),
              source: z
                .array(
                  z
                    .object({
                      end_time: z.number().describe('End time offset of the track cue in seconds'),
                      identifier: z
                        .union([z.string(), z.null()])
                        .describe('An identifier of the cue')
                        .default(null),
                      kind: z
                        .literal('track')
                        .describe('Identifies this type of source.')
                        .default('track'),
                      start_time: z
                        .number()
                        .describe('Start time offset of the track cue in seconds'),
                      voice: z
                        .union([z.string(), z.null()])
                        .describe('The name of the voice in this track (the speaker)')
                        .default(null),
                    })
                    .describe(
                      'Source metadata for a cue extracted from a media track.\n\nA `TrackSource` instance identifies a cue in a media track (audio, video, subtitles, screen-recording captions,\netc.). A *cue* here refers to any discrete segment that was pulled out of the original asset, e.g., a subtitle\nblock, an audio clip, or a timed marker in a screen-recording.',
                    ),
                )
                .describe(
                  'The provenance of this document item. Currently, it is only used for media track provenance.',
                )
                .default([]),
              text: z.string(),
            })
            .strict()
            .describe('TextItem.'),
        ]),
      )
      .default([]),
    version: z
      .string()
      .regex(
        new RegExp(
          '^(?<major>0|[1-9]\\d*)\\.(?<minor>0|[1-9]\\d*)\\.(?<patch>0|[1-9]\\d*)(?:-(?<prerelease>(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+(?<buildmetadata>[0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$',
        ),
      )
      .default('1.10.0'),
  })
  .describe('DoclingDocument.')
export type DoclingDocument = z.infer<typeof doclingDocument>
