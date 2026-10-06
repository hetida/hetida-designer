import { APIRequestContext } from '@playwright/test';
import { randomUUID } from 'node:crypto';

interface DesignerConfiguration {
  apiEndpoint: string;
}

interface IoDefinition {
  name: string;
  dataType: string;
}

export interface ComponentDefinition {
  name: string;
  category: string;
  description: string;
  versionTag: string;
  inputs: IoDefinition[];
  outputs: IoDefinition[];
  /** Replaces the `pass` placeholder in the generated entrypoint function. */
  functionBody: string;
  documentation: string;
  testWiring?: unknown;
}

interface IoInterface {
  inputs: { id: string; name: string; data_type: string }[];
  outputs: { id: string; name: string; data_type: string }[];
}

interface TransformationStub {
  id: string;
  name: string;
  version_tag: string;
  state: 'DRAFT' | 'RELEASED' | 'DISABLED';
  io_interface: IoInterface;
}

interface Transformation extends TransformationStub {
  documentation: string;
  content: string;
}

const withTrailingSlash = (url: string): string =>
  url.endsWith('/') ? url : `${url}/`;

/**
 * Backend client used for test housekeeping.
 *
 * Cleaning up through the rest api rather than the navigation menu keeps a
 * failing test from poisoning its own retries. Hetida identifies
 * transformations by uuid, so the same name and tag may exist many times: once
 * a ui cleanup leaves one behind, the next attempt adds a second copy and from
 * then on every locator for that name matches more than one element, which no
 * attempt can recover from.
 */
export class BackendApi {
  private constructor(
    private readonly request: APIRequestContext,
    private readonly apiUrl: string
  ) {}

  public static async create(
    request: APIRequestContext,
    baseUrl: string
  ): Promise<BackendApi> {
    // Ask the frontend where its backend is, so this keeps working against any
    // deployment. The configured endpoint may be absolute or relative.
    const configUrl = new URL(
      'assets/hetida_designer_config.json',
      withTrailingSlash(baseUrl)
    ).href;

    const response = await request.get(configUrl);
    if (!response.ok()) {
      throw new Error(
        `Could not read ${configUrl}: ${response.status()} ${response.statusText()}`
      );
    }

    const configuration = (await response.json()) as DesignerConfiguration;
    const apiUrl = new URL(
      configuration.apiEndpoint,
      withTrailingSlash(baseUrl)
    ).href;

    return new BackendApi(request, apiUrl.replace(/\/+$/, ''));
  }

  /**
   * Creates a released-ready draft component without touching the ui.
   *
   * Tests that are about something else - releasing, for instance - should not
   * have to click their fixture together through the create dialog, the io
   * dialog and the code editor first: that is a dozen steps in which nothing
   * they assert can fail, and each one is a chance to fail for an unrelated
   * reason. Creating a component through the ui is covered by its own test.
   *
   * The code is not written here. The backend generates the entrypoint from the
   * io interface, exactly as it does for a component created in the ui, and
   * only the placeholder body is replaced - so the generated COMPONENT_INFO
   * always matches the io interface.
   */
  public async createComponent(
    component: ComponentDefinition
  ): Promise<string> {
    const id = randomUUID();

    const created = await this.request.post(`${this.apiUrl}/transformations`, {
      data: {
        id,
        revision_group_id: randomUUID(),
        name: component.name,
        category: component.category,
        description: component.description,
        version_tag: component.versionTag,
        type: 'COMPONENT',
        state: 'DRAFT',
        documentation: component.documentation,
        io_interface: {
          inputs: component.inputs.map(input => ({
            id: randomUUID(),
            name: input.name,
            data_type: input.dataType
          })),
          outputs: component.outputs.map(output => ({
            id: randomUUID(),
            name: output.name,
            data_type: output.dataType
          }))
        },
        test_wiring: component.testWiring ?? {
          input_wirings: [],
          output_wirings: []
        },
        content: ''
      }
    });

    if (!created.ok()) {
      throw new Error(
        `Could not create ${component.name}: ${created.status()} ${await created.text()}`
      );
    }

    const generated = await this.request.get(
      `${this.apiUrl}/transformations/${id}`
    );
    if (!generated.ok()) {
      throw new Error(
        `Could not read back ${component.name}: ${generated.status()} ${generated.statusText()}`
      );
    }

    const transformation = (await generated.json()) as { content: string };
    const placeholder = '    pass';
    if (!transformation.content.includes(placeholder)) {
      throw new Error(
        `Generated component code for ${component.name} has no "${placeholder.trim()}" placeholder to replace`
      );
    }
    transformation.content = transformation.content.replace(
      placeholder,
      component.functionBody
        .split('\n')
        .map(line => `    ${line}`)
        .join('\n')
    );

    const updated = await this.request.put(
      `${this.apiUrl}/transformations/${id}`,
      { data: transformation }
    );
    if (!updated.ok()) {
      throw new Error(
        `Could not write code for ${component.name}: ${updated.status()} ${await updated.text()}`
      );
    }

    return id;
  }

  /**
   * Marks a draft as released, the way importing a released revision does.
   * Lets a test start from a released component without first clicking through
   * the publish dialog, which has its own test.
   */
  public async releaseComponent(id: string): Promise<void> {
    const transformation = await this.getTransformation(id);
    const response = await this.request.put(
      `${this.apiUrl}/transformations/${id}`,
      {
        data: {
          ...transformation,
          state: 'RELEASED',
          released_timestamp: new Date().toISOString()
        }
      }
    );

    if (!response.ok()) {
      throw new Error(
        `Could not release ${id}: ${response.status()} ${await response.text()}`
      );
    }
  }

  public async getTransformation(id: string): Promise<Transformation> {
    const response = await this.request.get(
      `${this.apiUrl}/transformations/${id}`
    );

    if (!response.ok()) {
      throw new Error(
        `Could not read transformation ${id}: ${response.status()} ${response.statusText()}`
      );
    }

    return (await response.json()) as Transformation;
  }

  /**
   * Removes every transformation revision with exactly this name, whatever its
   * state. Does nothing when there is none, so it is safe to call from an
   * afterEach hook of a test that failed before it created anything.
   */
  public async deleteTransformationsByName(name: string): Promise<void> {
    for (const transformation of await this.findTransformationsByName(name)) {
      // `ignore_state` also removes released and deprecated revisions.
      const response = await this.request.delete(
        `${this.apiUrl}/transformations/${transformation.id}`,
        { params: { ignore_state: 'true' } }
      );

      if (!response.ok()) {
        throw new Error(
          `Could not delete ${transformation.name} (${transformation.version_tag}), ` +
            `id ${transformation.id}: ${response.status()} ${response.statusText()}`
        );
      }
    }
  }

  public async findTransformationsByName(
    name: string
  ): Promise<TransformationStub[]> {
    const response = await this.request.get(
      `${this.apiUrl}/transformations/stubs`,
      { params: { name, include_deprecated: 'true' } }
    );

    if (!response.ok()) {
      throw new Error(
        `Could not look up transformations named "${name}": ` +
          `${response.status()} ${response.statusText()}`
      );
    }

    return (await response.json()) as TransformationStub[];
  }
}
