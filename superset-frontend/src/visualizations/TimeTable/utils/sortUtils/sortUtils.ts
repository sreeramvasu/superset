/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import type { ColumnConfig, Entry } from '../../types';
import { calculateCellValue } from '../valueCalculations/valueCalculations';

/**
 * Row shape provided by react-table, whose cell values are React elements
 * rendered by ValueCell or Sparkline.
 */
interface SortableRow {
  values?: Record<string, { props?: unknown } | undefined>;
}
/**
 * Simple numeric value comparison that handles null, undefined, and mixed types
 * @param a - First value to compare
 * @param b - Second value to compare
 * @param nanTreatment - How to treat NaN values
 * @returns Numeric comparison result
 */
function compareValues(
  a: number | string | null | undefined,
  b: number | string | null | undefined,
  nanTreatment: 'asSmallest' | 'asLargest' | 'alwaysLast' = 'asSmallest',
): number {
  const numA = typeof a === 'string' ? parseFloat(a) : a;
  const numB = typeof b === 'string' ? parseFloat(b) : b;

  const validA = numA != null && !Number.isNaN(numA) ? numA : undefined;
  const validB = numB != null && !Number.isNaN(numB) ? numB : undefined;

  if (validA === undefined && validB === undefined) return 0;
  if (validA === undefined) return nanTreatment === 'asSmallest' ? -1 : 1;
  if (validB === undefined) return nanTreatment === 'asSmallest' ? 1 : -1;

  return validA - validB;
}

/**
 * Sorts table rows with mixed data types for react-table.
 *
 * @param rowA - First row to compare
 * @param rowB - Second row to compare
 * @param columnId - Column identifier for sorting
 * @returns Numeric comparison result for react-table
 * react-table handles the asc/desc direction flip internally after calling
 * this function, so we only return the raw comparison result.
 */
export function sortNumberWithMixedTypes(
  rowA: SortableRow,
  rowB: SortableRow,
  columnId: string,
) {
  const cellA = rowA.values?.[columnId];
  const cellB = rowB.values?.[columnId];

  // Both ValueCell and Sparkline cells pass React elements here.
  // ValueCell provides the precomputed value directly.
  // Sparkline provides { valueField, column, entries } and requires
  // calculating the sortable value from its entries.
  const propsA = cellA?.props as
    | {
        value?: number | null;
        valueField?: string;
        column?: ColumnConfig;
        entries?: Entry[];
      }
    | undefined;

  const propsB = cellB?.props as
    | {
        value?: number | null;
        valueField?: string;
        column?: ColumnConfig;
        entries?: Entry[];
      }
    | undefined;

  if (!propsA || !propsB) {
    return 0;
  }

  // ValueCell already provides the computed value.
  if ('value' in propsA && 'value' in propsB) {
    return compareValues(propsA.value, propsB.value, 'asSmallest');
  }

  // Sparkline still needs calculation.
  const reversedEntriesA = propsA.entries?.slice().reverse();
  const reversedEntriesB = propsB.entries?.slice().reverse();

  if (
    !reversedEntriesA ||
    !reversedEntriesB ||
    !propsA.valueField ||
    !propsA.column ||
    !propsB.valueField ||
    !propsB.column
  ) {
    return 0;
  }

  const { value: valueA } = calculateCellValue(
    propsA.valueField,
    propsA.column,
    reversedEntriesA,
  );

  const { value: valueB } = calculateCellValue(
    propsB.valueField,
    propsB.column,
    reversedEntriesB,
  );

  return compareValues(valueA, valueB, 'asSmallest');
}
